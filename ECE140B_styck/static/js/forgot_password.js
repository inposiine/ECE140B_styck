document.getElementById('resetPasswordForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;

    try {
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        });

        const data = await response.json();

        if (response.ok) {
            alert('Password reset email sent! Please check your inbox.');
            window.location.href = '/';
        } else {
            alert(data.message || 'Failed to send reset email');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request');
    }
}); 