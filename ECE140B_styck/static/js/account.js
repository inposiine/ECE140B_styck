document.addEventListener('DOMContentLoaded', () => {
    const createAccountRadio = document.getElementById('createAccount');
    const changePasswordRadio = document.getElementById('changePassword');
    const createAccountFields = document.getElementById('createAccountFields');
    const changePasswordFields = document.getElementById('changePasswordFields');

    // Handle radio button changes
    createAccountRadio.addEventListener('change', () => {
        createAccountFields.style.display = 'block';
        changePasswordFields.style.display = 'none';
    });

    changePasswordRadio.addEventListener('change', () => {
        createAccountFields.style.display = 'none';
        changePasswordFields.style.display = 'block';
    });

    // Handle form submission
    document.getElementById('accountForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        if (createAccountRadio.checked) {
            // Create account logic
            const username = document.getElementById('newUsername').value;
            const password = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (password !== confirmPassword) {
                alert('Passwords do not match');
                return;
            }

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password }),
                });

                const data = await response.json();
                if (response.ok) {
                    alert('Account created successfully!');
                    window.location.href = '/';
                } else {
                    alert(data.message || 'Account creation failed');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during account creation');
            }
        } else {
            // Change password logic
            const username = document.getElementById('existingUsername').value;
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPasswordChange').value;

            try {
                const response = await fetch('/api/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, currentPassword, newPassword }),
                });

                const data = await response.json();
                if (response.ok) {
                    alert('Password changed successfully!');
                    window.location.href = '/';
                } else {
                    alert(data.message || 'Password change failed');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during password change');
            }
        }
    });
}); 