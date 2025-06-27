// Countdown Timer
function updateCountdown() {
    const eventDate = new Date('2025-08-17T00:00:00').getTime();
    const now = new Date().getTime();
    const timeLeft = eventDate - now;

    if (timeLeft > 0) {
        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

        document.getElementById('days').textContent = String(days).padStart(2, '0');
        document.getElementById('hours').textContent = String(hours).padStart(2, '0');
        document.getElementById('minutes').textContent = String(minutes).padStart(2, '0');
        document.getElementById('seconds').textContent = String(seconds).padStart(2, '0');
    } else {
        document.getElementById('days').textContent = '00';
        document.getElementById('hours').textContent = '00';
        document.getElementById('minutes').textContent = '00';
        document.getElementById('seconds').textContent = '00';
    }
}

// Update countdown every second
setInterval(updateCountdown, 1000);
updateCountdown(); // Initial call

// Amount buttons
document.querySelectorAll('.amount-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const amount = this.dataset.amount;
        document.querySelector('input[name="amount"]').value = amount;
        
        // Remove active class from all buttons
        document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('btn-warning'));
        // Add active class to clicked button
        this.classList.add('btn-warning');
    });
});

// Form submission
document.getElementById('contribution-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = {
        full_name: formData.get('full_name'),
        phone_number: formData.get('phone_number'),
        amount: parseFloat(formData.get('amount'))
    };

    // Validate form
    if (!data.full_name || !data.phone_number || !data.amount) {
        document.getElementById('error_message').textContent = 'Please fill in all fields';
        document.getElementById('error_modal').showModal();
        return;
    }

    if (data.amount < 1) {
        document.getElementById('error_message').textContent = 'Amount must be at least Ksh. 1';
        document.getElementById('error_modal').showModal();
        return;
    }

    // Show loading modal
    document.getElementById('loading_modal').showModal();
    
    try {
        const response = await fetch('{% url "camp_meeting:contribute" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        // Close loading modal
        document.getElementById('loading_modal').close();

        if (result.success) {
            document.getElementById('success_modal').showModal();
            // Reset form
            this.reset();
            document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('btn-warning'));
            
            // Update stats after successful contribution
            setTimeout(updateStats, 2000);
        } else {
            document.getElementById('error_message').textContent = result.message || 'Payment failed. Please try again.';
            document.getElementById('error_modal').showModal();
        }
    } catch (error) {
        // Close loading modal
        document.getElementById('loading_modal').close();
        document.getElementById('error_message').textContent = 'Network error. Please check your connection and try again.';
        document.getElementById('error_modal').showModal();
    }
});

// Update stats every 20 seconds
setInterval(updateStats, 20000);

// Smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Update statistics
async function updateStats() {
    try {
        const response = await fetch('{% url "camp_meeting:stats" %}');
        const data = await response.json();
        
        // Update displayed values
        document.getElementById('total-raised').textContent = `Ksh. ${data.total_contributions.toLocaleString()}`;
        document.getElementById('days-left').textContent = data.countdown.days;
        
        // Update progress bar
        const progressBar = document.querySelector('.progress-custom');
        progressBar.style.width = `${data.percentage_raised}%`;
        
        // Update countdown
        document.getElementById('days').textContent = String(data.countdown.days).padStart(2, '0');
        document.getElementById('hours').textContent = String(data.countdown.hours).padStart(2, '0');
        document.getElementById('minutes').textContent = String(data.countdown.minutes).padStart(2, '0');
        document.getElementById('seconds').textContent = String(data.countdown.seconds).padStart(2, '0');
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Real-time form validation
document.querySelector('input[name="amount"]').addEventListener('input', function(e) {
    const value = parseFloat(e.target.value);
    const submitBtn = document.getElementById('submit-btn');
    
    if (value < 1) {
        submitBtn.disabled = true;
        submitBtn.classList.add('btn-disabled');
    } else {
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-disabled');
    }
});

// Add loading animation to progress bar
document.addEventListener('DOMContentLoaded', function() {
    const progressBar = document.querySelector('.progress-custom');
    progressBar.style.width = '0%';
    
    setTimeout(() => {
        progressBar.style.width = '{{ percentage_raised }}%';
    }, 500);
});

// Add entrance animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in-up');
        }
    });
}, observerOptions);

// Observe all cards and sections
document.querySelectorAll('.card, .stat, section').forEach(el => {
    observer.observe(el);
});