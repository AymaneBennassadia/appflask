from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# File to store data
DATA_FILE = "cnc_exams.json"

# Constants
SUBJECTS = ['math1', 'math2', 'pc1', 'pc2', 'chimie', 'ge', 'gm']
CURRENT_YEAR = datetime.now().year
YEARS = list(range(2010, 2024 + 1))  # From 2010 to 2024 (14 exams per subject)

# Initialize data
def initialize_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    # Ensure each subject has exams for years 2010 to 2024
    for subject in SUBJECTS:
        if subject not in data:
            data[subject] = []
        existing_years = {exam['year'] for exam in data[subject]}
        for year in YEARS:
            if str(year) not in existing_years:
                data[subject].append({
                    'year': str(year),
                    'notes': '',
                    'completed': False,
                    'added_date': datetime.now().strftime("%Y-%m-%d")
                })
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return data

# Calculate statistics
def calculate_statistics(data):
    stats = {
        'subjects': {},
        'total': {'completed': 0, 'total': 0}
    }
    
    for subject in SUBJECTS:
        subject_exams = data.get(subject, [])
        completed = sum(1 for exam in subject_exams if exam['completed'])
        total = len(subject_exams)  # This should be 14 per subject
        
        stats['subjects'][subject] = {
            'completed': completed,
            'total': total,
            'percentage': (completed / total * 100) if total > 0 else 0
        }
        
        stats['total']['completed'] += completed
        stats['total']['total'] += total
    
    stats['total']['percentage'] = (stats['total']['completed'] / stats['total']['total'] * 100) if stats['total']['total'] > 0 else 0
    
    return stats

# Routes
@app.route('/')
def index():
    data = initialize_data()
    stats = calculate_statistics(data)
    return render_template('index.html', 
                         subjects=SUBJECTS, 
                         stats=stats,
                         current_year=CURRENT_YEAR)

@app.route('/subject/<subject>')
def subject_view(subject):
    if subject not in SUBJECTS:
        flash('Invalid subject', 'danger')
        return redirect(url_for('index'))
    
    data = initialize_data()
    exams = sorted(data[subject], key=lambda x: int(x['year']), reverse=True)
    stats = calculate_statistics(data)
    
    return render_template('subject.html', 
                         subject=subject, 
                         exams=exams,
                         subject_stats=stats['subjects'][subject])

@app.route('/add_exam', methods=['POST'])
def add_exam():
    subject = request.form.get('subject').lower()
    year = request.form.get('year')
    notes = request.form.get('notes', '')
    
    if subject not in SUBJECTS:
        flash('Invalid subject', 'danger')
        return redirect(url_for('index'))
    
    if not year.isdigit() or int(year) < 2010 or int(year) > 2024:
        flash(f'Year must be between 2010 and 2024', 'danger')
        return redirect(url_for('index'))
    
    data = initialize_data()
    
    # Check if exam exists
    for exam in data[subject]:
        if exam['year'] == year:
            flash(f'Exam for {subject} in {year} already exists!', 'warning')
            return redirect(url_for('index'))
    
    data[subject].append({
        'year': year,
        'notes': notes,
        'completed': False,
        'added_date': datetime.now().strftime("%Y-%m-%d")
    })
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    
    flash(f'Exam for {subject.upper()} in {year} added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/mark_completed', methods=['POST'])
def mark_completed():
    subject = request.form.get('subject').lower()
    year = request.form.get('year')
    
    data = initialize_data()
    
    for exam in data[subject]:
        if exam['year'] == year:
            if exam['completed']:
                flash(f'Exam for {subject.upper()} in {year} was already completed!', 'warning')
            else:
                exam['completed'] = True
                exam['completed_date'] = datetime.now().strftime("%Y-%m-%d")
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f, indent=4)
                flash(f'Exam for {subject.upper()} in {year} marked as completed!', 'success')
            return redirect(url_for('subject_view', subject=subject))
    
    flash(f'No exam found for {subject.upper()} in {year}', 'danger')
    return redirect(url_for('index'))

@app.route('/update_notes', methods=['POST'])
def update_notes():
    subject = request.form.get('subject').lower()
    year = request.form.get('year')
    new_notes = request.form.get('notes', '')
    
    data = initialize_data()
    
    for exam in data[subject]:
        if exam['year'] == year:
            exam['notes'] = new_notes
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            flash(f'Notes updated for {subject.upper()} {year}!', 'success')
            return redirect(url_for('subject_view', subject=subject))
    
    flash(f'No exam found for {subject.upper()} in {year}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create base template
    if not os.path.exists('templates/base.html'):
        with open('templates/base.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNC Exam Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
        }
        .progress-bar {
            transition: width 0.6s ease;
        }
        .exam-card {
            transition: all 0.3s ease;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .exam-card:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        }
        .notes-edit {
            display: none;
        }
        .editing .notes-display {
            display: none;
        }
        .editing .notes-edit {
            display: block;
        }
        .sticky-nav {
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .completed {
            background-color: #28a745;
            color: white;
        }
        .pending {
            background-color: #ffc107;
            color: white;
        }
        .card-header {
            background-color: #f8f9fa;
        }
        .card-footer {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary sticky-nav mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">CNC Exam Tracker</a>
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function toggleEdit(examId) {
            const examElement = document.getElementById(examId);
            examElement.classList.toggle('editing');
        }
    </script>
</body>
</html>''')
    
    # Create index template
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write('''{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <h2 class="mb-4">Your Progress</h2>
        
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                Overall Statistics
            </div>
            <div class="card-body">
                <h5 class="card-title">
                    {{ "%.1f"|format(stats.total.percentage) }}% Complete
                </h5>
                <div class="progress mb-3">
                    <div class="progress-bar bg-success" role="progressbar" 
                         style="width: {{ stats.total.percentage }}%" 
                         aria-valuenow="{{ stats.total.percentage }}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
                <p class="card-text">
                    <strong>{{ stats.total.completed }}</strong> of <strong>{{ stats.total.total }}</strong> exams completed
                </p>
            </div>
        </div>

        <div class="row">
            {% for subject, stat in stats.subjects.items() %}
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-header bg-secondary text-white">
                        {{ subject.upper() }}
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">
                            {{ "%.1f"|format(stat.percentage) }}% Complete
                        </h5>
                        <div class="progress mb-3">
                            <div class="progress-bar 
                                {% if stat.percentage > 75 %}bg-success
                                {% elif stat.percentage > 50 %}bg-info
                                {% elif stat.percentage > 25 %}bg-warning
                                {% else %}bg-danger{% endif %}" 
                                role="progressbar" 
                                style="width: {{ stat.percentage }}%" 
                                aria-valuenow="{{ stat.percentage }}" 
                                aria-valuemin="0" 
                                aria-valuemax="100">
                            </div>
                        </div>
                        <p class="card-text">
                            <strong>{{ stat.completed }}</strong> of <strong>{{ stat.total }}</strong> exams completed
                        </p>
                        <a href="{{ url_for('subject_view', subject=subject) }}" class="btn btn-primary btn-sm">
                            View Exams
                        </a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="col-md-4">
        <div class="card">
            <div class="card-header bg-primary text-white">
                Add New Exam
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('add_exam') }}">
                    <div class="mb-3">
                        <label for="subject" class="form-label">Subject</label>
                        <select class="form-select" id="subject" name="subject" required>
                            <option value="">Select a subject</option>
                            {% for subject in subjects %}
                                <option value="{{ subject }}">{{ subject.upper() }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="year" class="form-label">Year</label>
                        <input type="number" class="form-control" id="year" name="year" 
                               min="2010" max="2024" required>
                    </div>
                    <div class="mb-3">
                        <label for="notes" class="form-label">Notes (optional)</label>
                        <textarea class="form-control" id="notes" name="notes" rows="2"></textarea>
                    </div>
                    <button type="submit" class="btn btn-success">
                        Add Exam
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}''')

    # Create subject template
    if not os.path.exists('templates/subject.html'):
        with open('templates/subject.html', 'w') as f:
            f.write('''{% extends "base.html" %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>{{ subject.upper() }} Exams</h2>
    <a href="{{ url_for('index') }}" class="btn btn-outline-primary">
        Back to Dashboard
    </a>
</div>

<div class="card mb-4">
    <div class="card-header bg-secondary text-white">
        {{ subject.upper() }} Statistics
    </div>
    <div class="card-body">
        <h5 class="card-title">
            {{ "%.1f"|format(subject_stats.percentage) }}% Complete
        </h5>
        <div class="progress mb-3">
            <div class="progress-bar 
                {% if subject_stats.percentage > 75 %}bg-success
                {% elif subject_stats.percentage > 50 %}bg-info
                {% elif subject_stats.percentage > 25 %}bg-warning
                {% else %}bg-danger{% endif %}" 
                role="progressbar" 
                style="width: {{ subject_stats.percentage }}%" 
                aria-valuenow="{{ subject_stats.percentage }}" 
                aria-valuemin="0" 
                aria-valuemax="100">
            </div>
        </div>
        <p class="card-text">
            <strong>{{ subject_stats.completed }}</strong> of <strong>{{ subject_stats.total }}</strong> exams completed
        </p>
    </div>
</div>

<div class="row">
    {% for exam in exams %}
    <div class="col-md-6 mb-3" id="exam-{{ exam.year }}">
        <div class="card h-100 {% if exam.completed %}border-success{% else %}border-warning{% endif %}">
            <div class="card-header {% if exam.completed %}bg-success text-white{% else %}bg-warning{% endif %}">
                {{ exam.year }} - {% if exam.completed %}Completed{% else %}Pending{% endif %}
            </div>
            <div class="card-body">
                <div class="notes-display">
                    {% if exam.notes %}
                    <p class="card-text">{{ exam.notes }}</p>
                    {% else %}
                    <p class="card-text text-muted">No notes added</p>
                    {% endif %}
                </div>
                <div class="notes-edit">
                    <form method="POST" action="{{ url_for('update_notes') }}">
                        <input type="hidden" name="subject" value="{{ subject }}">
                        <input type="hidden" name="year" value="{{ exam.year }}">
                        <textarea class="form-control mb-2" name="notes" rows="3">{{ exam.notes }}</textarea>
                        <button type="submit" class="btn btn-primary btn-sm">Save</button>
                        <button type="button" class="btn btn-secondary btn-sm" onclick="toggleEdit('exam-{{ exam.year }}')">Cancel</button>
                    </form>
                </div>
                <p class="card-text">
                    <small class="text-muted">
                        {% if exam.completed and exam.completed_date %}
                        <br>Completed on: {{ exam.completed_date }}
                        {% endif %}
                    </small>
                </p>
            </div>
            <div class="card-footer bg-transparent d-flex justify-content-between">
                {% if not exam.completed %}
                <form method="POST" action="{{ url_for('mark_completed') }}" class="d-inline">
                    <input type="hidden" name="subject" value="{{ subject }}">
                    <input type="hidden" name="year" value="{{ exam.year }}">
                    <button type="submit" class="btn btn-success btn-sm">
                        Mark Completed
                    </button>
                </form>
                {% endif %}
                <button class="btn btn-info btn-sm" onclick="toggleEdit('exam-{{ exam.year }}')">
                    Edit Notes
                </button>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}''')

    app.run(debug=True)
