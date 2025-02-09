document.addEventListener('DOMContentLoaded', function() {
    // Initialize date picker
    flatpickr("#date", {
        dateFormat: "d/m/Y",
        minDate: "today"
    });

    // Initialize time picker
    flatpickr("#time", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: true
    });

    // Handle "All Categories" checkbox
    document.getElementById('allCategories').addEventListener('change', function() {
        const specificCategories = document.getElementById('specificCategories');
        const categoryCheckboxes = document.querySelectorAll('.category-checkbox');
        
        if (this.checked) {
            specificCategories.style.display = 'none';
            categoryCheckboxes.forEach(cb => cb.checked = false);
        } else {
            specificCategories.style.display = 'block';
        }
    });

    // Handle filter buttons
    const filterButtons = document.querySelectorAll('[data-filter]');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Filter reminders
            const filter = this.getAttribute('data-filter');
            filterReminders(filter);
        });
    });

    // Load existing reminders
    loadReminders();

    // Handle form submission
    document.getElementById('reminderForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get selected categories
        let categories;
        if (document.getElementById('allCategories').checked) {
            categories = ['all'];
        } else {
            categories = Array.from(document.querySelectorAll('.category-checkbox:checked'))
                .map(cb => cb.value);
            if (categories.length === 0) {
                alert('Please select at least one category');
                return;
            }
        }

        const reminder = {
            date: document.getElementById('date').value,
            time: document.getElementById('time').value,
            message: document.getElementById('message').value,
            categories: categories.join(',')
        };

        try {
            const response = await fetch('/api/reminders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reminder)
            });

            if (response.ok) {
                // Clear form
                this.reset();
                document.getElementById('allCategories').checked = true;
                document.getElementById('specificCategories').style.display = 'none';
                // Reload reminders
                loadReminders();
                alert('Reminder added successfully!');
            } else {
                alert('Failed to add reminder');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add reminder');
        }
    });
});

async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        
        const remindersList = document.getElementById('remindersList');
        remindersList.innerHTML = '';

        reminders.forEach(reminder => {
            const item = document.createElement('div');
            item.className = 'list-group-item reminder-item';
            item.setAttribute('data-categories', reminder.categories);
            
            // Create category badges
            const categories = reminder.categories.split(',');
            const categoryBadges = categories.map(category => 
                `<span class="badge bg-primary me-1">${category.toUpperCase()}</span>`
            ).join('');

            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="reminder-time">📅 ${reminder.date} at ${reminder.time}</div>
                        <div class="reminder-message">${reminder.message}</div>
                        <div class="reminder-categories mt-2">
                            ${categoryBadges}
                        </div>
                    </div>
                    <button class="btn btn-danger btn-sm delete-reminder" 
                            onclick="deleteReminder(${reminder.id})">
                        Delete
                    </button>
                </div>
            `;
            remindersList.appendChild(item);
        });

        // Apply current filter
        const activeFilter = document.querySelector('[data-filter].active').getAttribute('data-filter');
        filterReminders(activeFilter);
    } catch (error) {
        console.error('Error:', error);
    }
}

function filterReminders(filter) {
    const reminders = document.querySelectorAll('.reminder-item');
    
    reminders.forEach(reminder => {
        const categories = reminder.getAttribute('data-categories').split(',');
        if (filter === 'all' || categories.includes('all') || categories.includes(filter)) {
            reminder.style.display = 'block';
        } else {
            reminder.style.display = 'none';
        }
    });
}

async function deleteReminder(id) {
    if (!confirm('Are you sure you want to delete this reminder?')) {
        return;
    }

    try {
        const response = await fetch(`/api/reminders/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadReminders();
        } else {
            alert('Failed to delete reminder');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to delete reminder');
    }
}
