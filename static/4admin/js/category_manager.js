// script.js
document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.getElementById('addBtn');
    const modal = document.getElementById('addCategoryModal');
    const closeModal = document.getElementsByClassName('close')[0];
    const addCategoryForm = document.getElementById('addCategoryForm');
    const categoryTable = document.getElementById('categoryTable');

    addBtn.onclick = function() {
        modal.style.display = "block";
    }

    closeModal.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    addCategoryForm.onsubmit = function(e) {
        e.preventDefault();
        const name = document.getElementById('name').value;
        const description = document.getElementById('description').value;

        // Here you would typically send the data to a server
        // For this example, we'll just add it to the table
        const newRow = categoryTable.insertRow(-1);
        newRow.insertCell(0).innerHTML = 'New ID'; // Replace 'New ID' with actual ID
        newRow.insertCell(1).innerHTML = name;
        newRow.insertCell(2).innerHTML = description;
        newRow.insertCell(3).innerHTML = '<button>Edit</button> <button>Delete</button>';

        modal.style.display = "none";
    }
});
