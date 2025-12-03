// Community

function toggleFollow(username, btn) {
  console.log('toggleFollow called for:', username);
  fetch(`/tips/follow/${username}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
  })
    .then(response => {
      if (response.status === 401) {
        window.location.href = "{% url 'accounts:login' %}";
        return;
      }
      return response.json();
    })
    .then(data => {
      if (data) {
        const span = btn.querySelector('span');

        if (data.is_following) {
          btn.classList.remove('bg-emerald-500', 'hover:bg-emerald-600', 'text-white');
          btn.classList.add(
            'bg-gray-100', 'dark:bg-gray-800',
            'hover:bg-gray-200', 'dark:hover:bg-gray-700',
            'text-gray-900', 'dark:text-white'
          );
          span.textContent = 'Following';
        } else {
          btn.classList.remove(
            'bg-gray-100', 'dark:bg-gray-800',
            'hover:bg-gray-200', 'dark:hover:bg-gray-700',
            'text-gray-900', 'dark:text-white'
          );
          btn.classList.add('bg-emerald-500', 'hover:bg-emerald-600', 'text-white');
          span.textContent = 'Follow';
        }

        const countEl = document.getElementById(`follower-count-${username}`);
        if (countEl) {
          countEl.textContent = data.followers_count;
        }

        // Real-time card movement for Community page
        const card = document.getElementById(`user-card-${username}`);
        const discoverGrid = document.getElementById('discover-people-grid');
        const communityGrid = document.getElementById('your-community-grid');
        const discoverSection = document.getElementById('discover-people-section');
        const communitySection = document.getElementById('your-community-section');
        const noUsersMsg = document.getElementById('no-users-found');

        console.log('Elements found:', { card, discoverGrid, communityGrid });

        if (card && discoverGrid && communityGrid) {
          console.log('Moving card. is_following:', data.is_following);
          if (data.is_following) {
            communityGrid.appendChild(card);
          } else {
            discoverGrid.appendChild(card);
          }

          // Update section visibility
          if (discoverGrid.children.length === 0) {
            discoverSection.classList.add('hidden');
          } else {
            discoverSection.classList.remove('hidden');
          }

          if (communityGrid.children.length === 0) {
            communitySection.classList.add('hidden');
          } else {
            communitySection.classList.remove('hidden');
          }

          // Update empty state visibility
          if (discoverGrid.children.length === 0 && communityGrid.children.length === 0) {
            noUsersMsg.classList.remove('hidden');
          } else {
            noUsersMsg.classList.add('hidden');
          }
        }
      }
    });
}


//Like and bookmark toggle

function toggleLike(slug) {
  const csrftoken = getCookie('csrftoken');

  fetch(`/tips/${slug}/like/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Content-Type': 'application/json',
    },
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById('likesCount').textContent = data.likes_count;

      const button = document.getElementById('likeButton');
      const buttonText = document.getElementById('likeButtonText');
      const svg = button.querySelector('svg');

      if (data.liked) {
        svg.classList.add('text-red-500', 'fill-current');
        svg.classList.remove('text-gray-600', 'dark:text-gray-400');
        svg.setAttribute('fill', 'currentColor');
        buttonText.classList.add('text-red-500');
        buttonText.classList.remove('text-gray-600', 'dark:text-gray-400');
        buttonText.textContent = 'Liked';
      } else {
        svg.classList.remove('text-red-500', 'fill-current');
        svg.classList.add('text-gray-600', 'dark:text-gray-400');
        svg.setAttribute('fill', 'none');
        buttonText.classList.remove('text-red-500');
        buttonText.classList.add('text-gray-600', 'dark:text-gray-400');
        buttonText.textContent = 'Like';
      }
    })
    .catch(error => console.error('Error:', error));
}

function toggleBookmark(slug) {
  const csrftoken = getCookie('csrftoken');

  fetch(`/tips/${slug}/bookmark/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Content-Type': 'application/json',
    },
  })
    .then(response => response.json())
    .then(data => {
      const button = document.getElementById('bookmarkButton');
      const buttonText = document.getElementById('bookmarkButtonText');
      const svg = button.querySelector('svg');

      if (data.bookmarked) {
        svg.classList.add('text-yellow-500', 'fill-current');
        svg.classList.remove('text-gray-600', 'dark:text-gray-400');
        svg.setAttribute('fill', 'currentColor');
        buttonText.classList.add('text-yellow-500');
        buttonText.classList.remove('text-gray-600', 'dark:text-gray-400');
        buttonText.textContent = 'Saved';
      } else {
        svg.classList.remove('text-yellow-500', 'fill-current');
        svg.classList.add('text-gray-600', 'dark:text-gray-400');
        svg.setAttribute('fill', 'none');
        buttonText.classList.remove('text-yellow-500');
        buttonText.classList.add('text-gray-600', 'dark:text-gray-400');
        buttonText.textContent = 'Save';
      }
    })
    .catch(error => console.error('Error:', error));
}


// Tips category toggle in sidebar
// Category toggle functionality
document.addEventListener('DOMContentLoaded', function () {
  const existingBtn = document.getElementById('existingCategoryBtn');
  const newBtn = document.getElementById('newCategoryBtn');
  const existingSection = document.getElementById('existingCategorySection');
  const newSection = document.getElementById('newCategorySection');
  const categorySelect = document.getElementById('id_category');

  // Toggle to existing category
  existingBtn.addEventListener('click', function () {
    // Update button styles
    existingBtn.classList.add('bg-emerald-100', 'dark:bg-emerald-900', 'text-emerald-700', 'dark:text-emerald-300', 'border-emerald-500');
    existingBtn.classList.remove('bg-gray-100', 'dark:bg-gray-800', 'text-gray-700', 'dark:text-gray-300', 'border-transparent');

    newBtn.classList.remove('bg-emerald-100', 'dark:bg-emerald-900', 'text-emerald-700', 'dark:text-emerald-300', 'border-emerald-500');
    newBtn.classList.add('bg-gray-100', 'dark:bg-gray-800', 'text-gray-700', 'dark:text-gray-300', 'border-transparent');

    // Show/hide sections
    existingSection.classList.remove('hidden');
    newSection.classList.add('hidden');

    // Clear new category fields
    document.getElementById('id_new_category_name').value = '';
    document.getElementById('id_new_category_icon').value = '';
    document.getElementById('id_new_category_description').value = '';
  });

  // Toggle to new category
  newBtn.addEventListener('click', function () {
    // Update button styles
    newBtn.classList.add('bg-emerald-100', 'dark:bg-emerald-900', 'text-emerald-700', 'dark:text-emerald-300', 'border-emerald-500');
    newBtn.classList.remove('bg-gray-100', 'dark:bg-gray-800', 'text-gray-700', 'dark:text-gray-300', 'border-transparent');

    existingBtn.classList.remove('bg-emerald-100', 'dark:bg-emerald-900', 'text-emerald-700', 'dark:text-emerald-300', 'border-emerald-500');
    existingBtn.classList.add('bg-gray-100', 'dark:bg-gray-800', 'text-gray-700', 'dark:text-gray-300', 'border-transparent');

    // Show/hide sections
    existingSection.classList.add('hidden');
    newSection.classList.remove('hidden');

    // Clear existing category selection
    if (categorySelect) {
      categorySelect.selectedIndex = 0;
    }
  });
});


// Tips list
function toggleLikeTipList(slug) {
  fetch(`/tips/${slug}/like/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
  })
    .then(response => {
      if (response.status === 401) {
        window.location.href = "{% url 'accounts:login' %}";
        return;
      }
      return response.json();
    })
    .then(data => {
      if (data) {
        const icon = document.getElementById(`like-icon-${slug}`);
        const count = document.getElementById(`like-count-${slug}`);

        if (data.liked) {
          icon.classList.remove('text-gray-500', 'dark:text-gray-400');
          icon.classList.add('text-red-500', 'fill-current');
          icon.setAttribute('fill', 'currentColor');
        } else {
          icon.classList.remove('text-red-500', 'fill-current');
          icon.classList.add('text-gray-500', 'dark:text-gray-400');
          icon.setAttribute('fill', 'none');
        }

        count.textContent = data.likes_count;
      }
    });
}

function toggleBookmarkTipList(slug) {
  fetch(`/tips/${slug}/bookmark/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
  })
    .then(response => {
      if (response.status === 401) {
        window.location.href = "{% url 'accounts:login' %}";
        return;
      }
      return response.json();
    })
    .then(data => {
      if (data) {
        const icon = document.getElementById(`bookmark-icon-${slug}`);

        if (data.bookmarked) {
          icon.classList.remove('text-gray-500', 'dark:text-gray-400');
          icon.classList.add('text-yellow-500', 'fill-current');
          icon.setAttribute('fill', 'currentColor');
        } else {
          icon.classList.remove('text-yellow-500', 'fill-current');
          icon.classList.add('text-gray-500', 'dark:text-gray-400');
          icon.setAttribute('fill', 'none');
        }
      }
    });
}