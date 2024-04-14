document.addEventListener("DOMContentLoaded", function() {
    var addBtn = document.getElementById('addBtn');
    var modal = document.getElementById('addCategoryModal');
    var closeModal = document.querySelector("#addCategoryModal .close");
    var editModal = document.getElementById('editCategoryModal');
    var closeEditModal = document.querySelector("#editCategoryModal .close");

    // Show add category modal when add button is clicked
    addBtn.onclick = function() {
        modal.style.display = "block";
    };

    // Hide add category modal when close button is clicked
    closeModal.onclick = function() {
        modal.style.display = "none";
    };

    // Hide add category modal when user clicks outside of it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };

    // Show edit category modal when edit button is clicked
    var editButtons = document.querySelectorAll('.editBtn');
    editButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            editModal.style.display = "block";
            // Fetch category details and populate the form fields for editing
            var categoryId = this.closest('tr').querySelector('td:first-child').innerText;
            var categoryName = this.closest('tr').querySelector('td:nth-child(2)').innerText;
            var categoryDescription = this.closest('tr').querySelector('td:nth-child(3)').innerText;
            document.getElementById('editCategoryId').value = categoryId;
            document.getElementById('editName').value = categoryName;
            document.getElementById('editDescription').value = categoryDescription;
        });
    });

    // Hide edit category modal when close button is clicked
    closeEditModal.onclick = function() {
        editModal.style.display = "none";
    };

    // Hide edit category modal when user clicks outside of it
    window.onclick = function(event) {
        if (event.target == editModal) {
            editModal.style.display = "none";
        }
    };

    // Handle form submission for adding category
    var addCategoryForm = document.getElementById('addCategoryForm');
    addCategoryForm.addEventListener('submit', function(event) {
        event.preventDefault();
        // Submit form via AJAX or fetch API
    });

    // Handle form submission for editing category
    var editCategoryForm = document.getElementById('editCategoryForm');
    editCategoryForm.addEventListener('submit', function(event) {
        event.preventDefault();
        // Submit form via AJAX or fetch API
    });
});
