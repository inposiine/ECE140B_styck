document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        console.log('Login response:', data); // Debug log

        if (response.ok) {
            if (data.user && data.user.id) {
                console.log('Storing user ID:', data.user.id); // Debug log
                localStorage.setItem('userId', data.user.id.toString());
                localStorage.setItem('username', data.user.username);
                if (data.user.weight) {
                    localStorage.setItem('userWeight', data.user.weight);
                }
            } else {
                console.error('No user ID in response:', data); // Debug log
                alert('Login response missing user ID');
                return;
            }
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                window.location.href = '/dashboard';
            }
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during login');
    }
});
