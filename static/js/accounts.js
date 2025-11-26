    // Followers_list
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function toggleFollowersInList(username, button) {
        const csrftoken = getCookie('csrftoken');

        fetch(`/accounts/follow/${username}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.is_following) {
                    // Now following
                    button.classList.remove('bg-emerald-500', 'hover:bg-emerald-600');
                    button.classList.add('bg-gray-200', 'dark:bg-gray-700', 'text-gray-900', 'dark:text-white', 'hover:bg-gray-300', 'dark:hover:bg-gray-600');
                    button.textContent = 'Following';
                    button.setAttribute('data-following', 'true');
                } else {
                    // Unfollowed
                    button.classList.remove('bg-gray-200', 'dark:bg-gray-700', 'text-gray-900', 'dark:text-white', 'hover:bg-gray-300', 'dark:hover:bg-gray-600');
                    button.classList.add('bg-emerald-500', 'hover:bg-emerald-600');
                    button.textContent = 'Follow';
                    button.setAttribute('data-following', 'false');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }



//     Following List

    function toggleFollowInList(username, button) {
        const csrftoken = getCookie('csrftoken');

        fetch(`/accounts/follow/${username}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.is_following) {
                    button.classList.remove('bg-emerald-500', 'hover:bg-emerald-600');
                    button.classList.add('bg-gray-200', 'dark:bg-gray-700', 'text-gray-900', 'dark:text-white');
                    button.textContent = 'Following';
                } else {
                    button.classList.add('bg-emerald-500', 'hover:bg-emerald-600');
                    button.classList.remove('bg-gray-200', 'dark:bg-gray-700', 'text-gray-900', 'dark:text-white');
                    button.textContent = 'Follow';
                }
            })
            .catch(error => console.error('Error:', error));
    }

    // Checking follow status for all users on page load
    document.addEventListener('DOMContentLoaded', function () {
        const followBtns = document.querySelectorAll('.follow-btn');
        followBtns.forEach(btn => {
            const username = btn.dataset.username;
        });
    });


// Profile

    document.addEventListener('DOMContentLoaded', function () {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');
    const editProfileBtn = document.querySelector('.edit-profile-btn');
    const cancelBtn = document.querySelector('.cancel-btn');

    function showSection(targetId) {
      sections.forEach(section => section.classList.add('hidden'));
      navLinks.forEach(link => link.classList.remove('active'));

      const targetSection = document.querySelector(`#${targetId}`);
      if (targetSection) {
        targetSection.classList.remove('hidden');
      }

      const activeLink = document.querySelector(`.nav-link[href="#${targetId}"]`);
      if (activeLink) {
        activeLink.classList.add('active');
      }
    }

    navLinks.forEach(link => {
      link.addEventListener('click', function (e) {
        const href = this.getAttribute('href');

        // Only intercept hash links (internal tabs)
        if (href.startsWith('#')) {
          e.preventDefault();
          const targetId = href.substring(1);
          showSection(targetId);
        }
      });
    });

    if (editProfileBtn) {
      editProfileBtn.addEventListener('click', function () {
        showSection('edit');
      });
    }

    if (cancelBtn) {
      cancelBtn.addEventListener('click', function () {
        showSection('profile');
      });
    }

    showSection('profile');
  });

<!-- Follow Script -->

  function toggleFollow(username) {
    const csrftoken = getCookie('csrftoken');

    fetch(`/accounts/follow/${username}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
      },
    })
      .then(response => response.json())
      .then(data => {
        const button = document.getElementById('followButton');
        const buttonText = document.getElementById('followButtonText');
        const followersCount = document.getElementById('followersCount');
        const followCount = document.getElementById('follow_count');

        // Update followers count
        followersCount.textContent = data.followers_count;
        followCount.textContent = data.followers_count;


        if (data.is_following) {
          // Now following
          button.classList.remove('bg-emerald-500', 'dark:bg-emerald-600', 'hover:bg-emerald-600', 'dark:hover:bg-emerald-700');
          button.classList.add('bg-gray-200', 'dark:bg-gray-700', 'text-gray-900', 'dark:text-white', 'hover:bg-gray-300', 'dark:hover:bg-gray-600');
          buttonText.textContent = 'Following';
        } else {
          // Unfollowed
          button.classList.remove('bg-gray-200', 'dark:bg-gray-700', 'text-gray-900', 'dark:text-white', 'hover:bg-gray-300', 'dark:hover:bg-gray-600');
          button.classList.add('bg-emerald-500', 'dark:bg-emerald-600', 'text-white', 'hover:bg-emerald-600', 'dark:hover:bg-emerald-700');
          buttonText.textContent = 'Follow';
        }
      })
      .catch(error => console.error('Error:', error));
  }


//   login

    function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');

    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      input.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  }

  

