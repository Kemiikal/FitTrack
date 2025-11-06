console.log("FitTrack loaded");

document.addEventListener('DOMContentLoaded', function () {
	let currentForm = null;
	const modalEl = document.getElementById('confirmDeleteModal');
	const itemNameEl = document.getElementById('confirm-delete-item-name');
	const confirmBtn = document.getElementById('confirmDeleteBtn');
	let bsModal = null;

	if (modalEl && typeof bootstrap !== 'undefined') {
		bsModal = new bootstrap.Modal(modalEl);
	}

	document.querySelectorAll('form.confirm-delete').forEach(function (form) {
		form.addEventListener('submit', function (e) {
			e.preventDefault();
			currentForm = form;
			const name = form.dataset.itemName || 'this item';
			if (itemNameEl) itemNameEl.textContent = name;
			if (bsModal) bsModal.show();
			else if (confirm('Are you sure you want to delete ' + name + '?')) currentForm.submit();
		});
	});

	if (confirmBtn) {
		confirmBtn.addEventListener('click', function () {
			if (currentForm) currentForm.submit();
			if (bsModal) bsModal.hide();
		});
	}
});
