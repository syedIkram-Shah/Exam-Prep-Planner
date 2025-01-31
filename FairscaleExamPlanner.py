import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def calculate_composite_weight(subject):
    """Calculate priority score with inverse relationships"""
    preparation = (100 - subject['preparation']) * 0.35  # Most impact (reverse)
    syllabus = subject['syllabus'] * 0.3  # Medium impact
    exam = subject['exam_weight'] * 0.15  # Medium impact
    difficulty = (100 - subject['difficulty']) * 0.20  # Least impact (reverse)
    return preparation + syllabus + exam + difficulty


def fairscale_exam_allocate(subjects, total_days):
    """FairScale allocation algorithm for exam prep"""
    # Initialize allocation
    for sub in subjects:
        sub['weight'] = calculate_composite_weight(sub)
        sub['claim'] = sub['weight'] * sub['desired_days']
        sub['allocated'] = 0  # Initialize

    total_claim = sum(sub['claim'] for sub in subjects)

    # First allocation pass
    for sub in subjects:
        sub['allocated'] = min(
            (sub['claim'] / total_claim) * total_days,
            sub['desired_days']
        )

    # Redistribute remaining days
    remaining = total_days - sum(sub['allocated'] for sub in subjects)
    iterations = 0

    while remaining > 0 and iterations < 10:
        candidates = [s for s in subjects if s['allocated'] < s['desired_days']]
        if not candidates:
            break

        total_weight = sum(s['weight'] for s in candidates)
        for sub in candidates:
            add_days = (sub['weight'] / total_weight) * remaining
            sub['allocated'] = min(
                sub['allocated'] + add_days,
                sub['desired_days']
            )

        remaining = total_days - sum(sub['allocated'] for sub in subjects)
        iterations += 1

    return subjects


# Initialize session state
if 'subjects' not in st.session_state:
    st.session_state.subjects = []

# UI Setup
st.title("📚 Exam Prep FairScale Planner")
total_days = st.number_input("Total Available Study Days", min_value=1, value=30)

# Subject input form
# Subject input form
# Subject input form
with st.form("subject_form"):
    st.subheader("Add a New Subject")

    # Subject selection with autosuggestion - Custom first
    subjects_list = ["Custom", "Surgery", "Medicine", "Gynae", "peads", "Chemistry", "Biology"]
    subject_name = st.selectbox("Select your subjects", subjects_list)

    # Custom subject input if "Custom" is selected
    if subject_name == "Custom":
        custom_name = st.text_input("Enter custom subject name")
        # Use custom name if provided, otherwise default
        subject_name = custom_name if custom_name else "Unnamed Subject"

    # Rest of the sliders and inputs remain the same...

    # Sliders for parameters with updated labels
    preparation = st.slider("Preparation done in %", 1, 100, 50, key="prep")
    syllabus_size = st.slider("Syllabus size", 1, 100, 70, key="syllabus")
    difficulty = st.slider("Difficulty level", 1, 100, 60, key="diff")
    exam_weight = st.slider("Exam Weightage in %", 1, 100, 80, key="exam")
    desired_days = st.number_input("Desired days you want to dedicate", min_value=1, value=7)

    # Add subject button
    if st.form_submit_button("Add Subject ➕"):
        if subject_name.strip():  # Check if name is not empty
            new_subject = {
                'name': subject_name,
                'preparation': preparation,
                'syllabus': syllabus_size,
                'difficulty': difficulty,
                'exam_weight': exam_weight,
                'desired_days': desired_days
            }
            st.session_state.subjects.append(new_subject)
        else:
            st.error("Please provide a valid subject name.")

# Display current subjects
if st.session_state.subjects:
    st.subheader("Your Subjects")
    df = pd.DataFrame(st.session_state.subjects)[['name', 'desired_days']]
    st.dataframe(df.rename(columns={'name': 'Subject', 'desired_days': 'Requested Days'}))
# Calculation and Results
if st.button("📊 Calculate Study Plan"):
    if not st.session_state.subjects:
        st.error("❌ Add at least one subject!")
    else:
        results = fairscale_exam_allocate(st.session_state.subjects.copy(), total_days)

        # Create results DataFrame
        result_df = pd.DataFrame(results)[['name', 'desired_days', 'allocated']]
        result_df['difference'] = result_df['allocated'] - result_df['desired_days']
        result_df['status'] = np.where(
            result_df['difference'] >= 0,
            "✅ Full Allocation",
            "⚠️ Reduced by " + (-result_df['difference']).round(1).astype(str) + " days"
        )

        # Format display
        result_df = result_df.rename(columns={
            'name': 'Subject',
            'desired_days': 'Requested',
            'allocated': 'Allocated'
        })

        # Show results
        st.subheader("📈 Allocation Results")
        cols = st.columns([3, 2])
        with cols[0]:
            st.dataframe(
                result_df.style.format({
                    'Requested': '{:.1f}',
                    'Allocated': '{:.1f}',
                    'difference': '{:.1f}'
                }).applymap(lambda x: 'color: green' if x >= 0 else 'color: red',
                            subset=['difference']),
                height=300
            )

        with cols[1]:
            # Pie chart
            fig1, ax1 = plt.subplots()
            ax1.pie(
                result_df['Allocated'],
                labels=result_df['Subject'],
                autopct='%1.1f%%',
                startangle=90,
                colors=plt.cm.Pastel1.colors
            )
            ax1.set_title("Time Distribution")
            st.pyplot(fig1)

        # Bar chart comparison
        st.subheader("📅 Requested vs Allocated Days")
        fig2, ax2 = plt.subplots()
        result_df.set_index('Subject')[['Requested', 'Allocated']].plot(
            kind='bar',
            ax=ax2,
            color=['#ff9999', '#66b3ff']
        )
        ax2.set_ylabel("Days")
        ax2.set_xlabel("")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig2)

        # Resource summary
        used_days = result_df['Allocated'].sum()
        st.success(f"📆 Total Days Used: {used_days:.1f} of {total_days} days")
        if used_days < total_days:
            st.info(f"⏳ Remaining Days: {total_days - used_days:.1f} (distribute manually)")