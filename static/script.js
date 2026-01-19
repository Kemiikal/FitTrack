let selectedExerciseData = null;

function updateEstimatedCalories() {
    const estimatedCaloriesEl = document.getElementById('estimated-calories');
    if (!estimatedCaloriesEl || !selectedExerciseData) {
        return;
    }

    const duration = parseFloat(document.getElementById('duration').value) || 0;
    const sets = parseFloat(document.getElementById('sets').value) || 0;
    const reps = parseFloat(document.getElementById('reps').value) || 0;
    const intensity = parseFloat(document.getElementById('intensity').value) || 1.0;

    
    if (selectedExerciseData.type === 'strength' && (sets <= 0 || reps <= 0)) {
        estimatedCaloriesEl.textContent = '0 kcal';
        return;
    }

    
    const caloriesPer30Min = selectedExerciseData.caloriesPerHour / 2;

    
    let effectiveDuration = duration;
    if (selectedExerciseData.type === 'strength' && duration === 0 && sets > 0) {
        effectiveDuration = sets * 1;
    }

    
    let calories = Math.floor((caloriesPer30Min * effectiveDuration) / 30);

    
    calories = Math.floor(calories * intensity);

    
    if (selectedExerciseData.type === 'strength' && sets > 0 && reps > 0) {
        
        const repsFactor = Math.min(1 + (reps - 10) * 0.05, 2.0);  
        calories = Math.floor(calories * repsFactor);
    }

    estimatedCaloriesEl.textContent = Math.max(calories, 0) + ' kcal';
}

function validateAddForm() {
    const addBtn = document.getElementById('add-workout-btn');
    if (!selectedExerciseData) {
        if (addBtn) addBtn.disabled = true;
        return;
    }

    const type = selectedExerciseData.type;
    if (type === 'cardio') {
        const duration = parseInt(document.getElementById('duration').value) || 0;
        if (duration <= 0) {
            if (addBtn) addBtn.disabled = true;
            return;
        }
    } else if (type === 'strength') {
        const sets = parseInt(document.getElementById('sets').value) || 0;
        const reps = parseInt(document.getElementById('reps').value) || 0;
        const weightVal = document.getElementById('weight') ? document.getElementById('weight').value.trim() : '';
        if (sets <= 0 || reps <= 0 || weightVal === '') {
            if (addBtn) addBtn.disabled = true;
            return;
        }
        const weight = parseFloat(weightVal);
        if (isNaN(weight) || weight < 0) {
            if (addBtn) addBtn.disabled = true;
            return;
        }
    }

    if (addBtn) addBtn.disabled = false;
}

document.addEventListener('DOMContentLoaded', function() {
    
    const mealSearchInput = document.getElementById('meal-search');
    const mealList = document.getElementById('meal-list');
    const mealOptions = mealList?.querySelectorAll('.meal-option');

    if (mealSearchInput && mealList) {
        mealSearchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            mealOptions.forEach(option => {
                option.style.display = option.dataset.name.toLowerCase().includes(query) ? '' : 'none';
            });
        });

        mealOptions.forEach(option => {
            option.addEventListener('click', function() {
                document.getElementById('meal-name-input').value = this.dataset.name;
                document.querySelector('input[name="calories"]').value = this.dataset.calories;
                document.querySelector('input[name="protein"]').value = this.dataset.protein;
                document.querySelector('input[name="carbs"]').value = this.dataset.carbs;
                document.querySelector('input[name="fats"]').value = this.dataset.fats;
                bootstrap.Modal.getInstance(document.getElementById('selectMealModal')).hide();
            });
        });
    }

    
    const workoutSearchInput = document.getElementById('workout-search');
    const workoutList = document.getElementById('workout-list');
    const workoutOptions = workoutList?.querySelectorAll('.workout-option');

    if (workoutSearchInput && workoutList) {
        workoutSearchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            workoutOptions.forEach(option => {
                const name = option.dataset.name.toLowerCase();
                const muscles = option.dataset.muscles.toLowerCase();
                const benefit = option.dataset.benefit ? option.dataset.benefit.toLowerCase() : '';
                const matches = name.includes(query) || muscles.includes(query) || benefit.includes(query);
                option.style.display = matches ? '' : 'none';
            });
        });

        workoutOptions.forEach(option => {
            option.addEventListener('click', function() {
                
                document.getElementById('workout-name-input').value = this.dataset.name;
                document.getElementById('selected-exercise-text').textContent = this.dataset.name;
                document.getElementById('add-workout-btn').disabled = false;

                
                const isCustom = this.dataset.isCustom === 'true';
                const isFromOtherExercises = this.closest('.mb-2 h6') && this.closest('.mb-2 h6').textContent.trim() === 'Other Exercises';

                
                selectedExerciseData = {
                    name: this.dataset.name,
                    type: this.dataset.type,
                    muscles: this.dataset.muscles,
                    caloriesPerHour: parseInt(this.dataset.caloriesPerHour) || 0
                };

                
                if (isCustom || isFromOtherExercises) {
                    document.getElementById('is_custom').value = 'true';
                    document.getElementById('custom_type').value = this.dataset.type;
                    document.getElementById('custom_muscle_groups').value = this.dataset.muscles || '';
                    document.getElementById('custom_calories_per_hour').value = this.dataset.caloriesPerHour || '0';
                } else {
                    document.getElementById('is_custom').value = 'false';
                    document.getElementById('custom_type').value = '';
                    document.getElementById('custom_muscle_groups').value = '';
                    document.getElementById('custom_calories_per_hour').value = '';
                }

                
                if (selectedExerciseData.type === 'cardio') {
                    document.querySelectorAll('.cardio-only').forEach(el => el.style.display = 'block');
                    document.querySelectorAll('.strength-only').forEach(el => el.style.display = 'none');
                    
                    document.getElementById('sets').value = '';
                    document.getElementById('reps').value = '';
                    if (document.getElementById('weight')) document.getElementById('weight').value = '';
                } else if (selectedExerciseData.type === 'strength') {
                    document.querySelectorAll('.cardio-only').forEach(el => el.style.display = 'none');
                    document.querySelectorAll('.strength-only').forEach(el => el.style.display = 'block');
                    
                    document.getElementById('duration').value = '';
                }

                
                if (isFromOtherExercises) {
                    if (selectedExerciseData.type === 'cardio') {
                        document.getElementById('duration').value = '30'; 
                    } else if (selectedExerciseData.type === 'strength') {
                        document.getElementById('sets').value = '3'; 
                        document.getElementById('reps').value = '10'; 
                    }
                    document.getElementById('intensity').value = '1.0'; 
                }

                
                updateEstimatedCalories();
                validateAddForm();

                
                const modal = bootstrap.Modal.getInstance(document.getElementById('selectWorkoutModal'));
                modal.hide();
            });
        });
    }

    
    const durationInput = document.getElementById('duration');
    const setsInput = document.getElementById('sets');
    const repsInput = document.getElementById('reps');
    const intensityInput = document.getElementById('intensity');

    if (durationInput) {
        durationInput.addEventListener('input', updateEstimatedCalories);
        durationInput.addEventListener('change', updateEstimatedCalories);
        durationInput.addEventListener('input', validateAddForm);
        durationInput.addEventListener('change', validateAddForm);
    }
    if (setsInput) {
        setsInput.addEventListener('input', updateEstimatedCalories);
        setsInput.addEventListener('change', updateEstimatedCalories);
        setsInput.addEventListener('input', validateAddForm);
        setsInput.addEventListener('change', validateAddForm);
    }
    if (repsInput) {
        repsInput.addEventListener('input', updateEstimatedCalories);
        repsInput.addEventListener('change', updateEstimatedCalories);
        repsInput.addEventListener('input', validateAddForm);
        repsInput.addEventListener('change', validateAddForm);
    }
    const weightInput = document.getElementById('weight');
    if (weightInput) {
        weightInput.addEventListener('input', validateAddForm);
        weightInput.addEventListener('change', validateAddForm);
    }
    if (intensityInput) {
        intensityInput.addEventListener('input', updateEstimatedCalories);
        intensityInput.addEventListener('change', updateEstimatedCalories);
    }

    
    const addCustomWorkoutBtn = document.getElementById('add-custom-workout-btn');
    const addCustomWorkoutModal = document.getElementById('addCustomWorkoutModal');
    const customWorkoutTypeSelect = document.getElementById('custom-workout-type');
    const saveCustomWorkoutBtn = document.getElementById('save-custom-workout-btn');

    if (addCustomWorkoutBtn) {
        addCustomWorkoutBtn.addEventListener('click', function() {
            
            const selectModal = bootstrap.Modal.getInstance(document.getElementById('selectWorkoutModal'));
            selectModal.hide();

            
            const customModal = new bootstrap.Modal(addCustomWorkoutModal);
            customModal.show();
        });
    }

    if (customWorkoutTypeSelect) {
        customWorkoutTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            const cardioFields = document.querySelectorAll('.custom-cardio-fields');
            const strengthFields = document.querySelectorAll('.custom-strength-fields');

            if (selectedType === 'cardio') {
                cardioFields.forEach(el => el.style.display = 'block');
                strengthFields.forEach(el => el.style.display = 'none');
                
                document.getElementById('custom-sets').value = '';
                document.getElementById('custom-reps').value = '';
            } else if (selectedType === 'strength') {
                cardioFields.forEach(el => el.style.display = 'none');
                strengthFields.forEach(el => el.style.display = 'block');
                
                document.getElementById('custom-duration').value = '';
            } else {
                cardioFields.forEach(el => el.style.display = 'none');
                strengthFields.forEach(el => el.style.display = 'none');
            }
        });
    }

    
    const customDurationInput = document.getElementById('custom-duration');
    const customSetsInput = document.getElementById('custom-sets');
    const customRepsInput = document.getElementById('custom-reps');
    const customIntensityInput = document.getElementById('custom-intensity');

    if (saveCustomWorkoutBtn) {
        saveCustomWorkoutBtn.addEventListener('click', function() {
            const name = document.getElementById('custom-workout-name').value.trim();
            const type = document.getElementById('custom-workout-type').value;
            const muscleGroups = document.getElementById('custom-muscle-groups').value.trim();
            const caloriesPerHour = parseInt(document.getElementById('custom-calories-per-hour').value) || 0;
            const duration = parseInt(document.getElementById('custom-duration').value) || 0;
            const sets = parseInt(document.getElementById('custom-sets').value) || 0;
            const reps = parseInt(document.getElementById('custom-reps').value) || 0;

            const intensity = parseFloat(document.getElementById('custom-intensity').value) || 1.0;

            if (!name || !type) {
                alert('Please fill in the exercise name and select a type.');
                return;
            }

            
            if (type === 'cardio' && duration <= 0) {
                alert('Please enter a duration greater than 0 for cardio exercises.');
                return;
            } else if (type === 'strength' && (sets <= 0 || reps <= 0)) {
                alert('Please enter sets and reps greater than 0 for strength exercises.');
                return;
            }

            
            document.getElementById('workout-name-input').value = name;
            document.getElementById('selected-exercise-text').textContent = name;

            
            document.getElementById('is_custom').value = 'true';
            document.getElementById('custom_type').value = type;
            document.getElementById('custom_muscle_groups').value = muscleGroups;
            document.getElementById('custom_calories_per_hour').value = caloriesPerHour;


            
            selectedExerciseData = {
                name: name,
                type: type,
                muscles: muscleGroups,
                caloriesPerHour: caloriesPerHour
            };

            
            if (type === 'cardio') {
                document.querySelectorAll('.cardio-only').forEach(el => el.style.display = 'block');
                document.querySelectorAll('.strength-only').forEach(el => el.style.display = 'none');
                document.getElementById('duration').value = duration;
                document.getElementById('sets').value = '';
                document.getElementById('reps').value = '';
                
                const form = document.getElementById('add-workout-btn').closest('form');
                if (form) form.submit();
            } else if (type === 'strength') {
                document.querySelectorAll('.cardio-only').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.strength-only').forEach(el => el.style.display = 'block');
                document.getElementById('sets').value = sets;
                document.getElementById('reps').value = reps;
                document.getElementById('duration').value = '';
                
                if (document.getElementById('weight')) {
                    document.getElementById('weight').focus();
                    alert('Please enter weight for this strength workout (enter 0 for bodyweight), then press Add Workout.');
                    validateAddForm();
                }
            }

            document.getElementById('intensity').value = intensity;

            
            const form = document.getElementById('add-workout-btn').closest('form');
            

            
            const customModal = bootstrap.Modal.getInstance(addCustomWorkoutModal);
            customModal.hide();

            
            document.getElementById('custom-workout-name').value = '';
            document.getElementById('custom-workout-type').value = '';
            document.getElementById('custom-muscle-groups').value = '';
            document.getElementById('custom-calories-per-hour').value = '';
            document.getElementById('custom-duration').value = '';
            document.getElementById('custom-sets').value = '';
            document.getElementById('custom-reps').value = '';
            document.getElementById('custom-intensity').value = '1.0';
            document.querySelectorAll('.custom-cardio-fields, .custom-strength-fields').forEach(el => el.style.display = 'none');
        });
    }

    
    let currentForm = null;
    const modalEl = document.getElementById('confirmDeleteModal');
    const itemNameEl = document.getElementById('confirm-delete-item-name');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const bsModal = modalEl && typeof bootstrap !== 'undefined' ? new bootstrap.Modal(modalEl) : null;

    document.querySelectorAll('form.confirm-delete').forEach(form => {
        form.addEventListener('submit', e => {
            e.preventDefault();
            currentForm = form;
            const name = form.dataset.itemName || 'this item';
            if (itemNameEl) itemNameEl.textContent = name;
            if (bsModal) bsModal.show();
            else if (confirm('Are you sure you want to delete ' + name + '?')) currentForm.submit();
        });
    });

    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            if (currentForm) {
                
                if (currentForm.id === 'bulk-delete-form') {
                    const selectedCheckboxes = [...document.querySelectorAll('.meal-checkbox:checked')];
                    currentForm.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
                    selectedCheckboxes.forEach(cb => {
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.name = 'meal_ids';
                        hiddenInput.value = cb.value;
                        currentForm.appendChild(hiddenInput);
                    });
                } else if (currentForm.id === 'bulk-delete-workout-form') {
                    const selectedCheckboxes = [...document.querySelectorAll('.workout-checkbox:checked')];
                    currentForm.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
                    selectedCheckboxes.forEach(cb => {
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.name = 'workout_ids';
                        hiddenInput.value = cb.value;
                        currentForm.appendChild(hiddenInput);
                    });
                } else if (currentForm.id === 'bulk-delete-notification-form') {
                    const selectedCheckboxes = [...document.querySelectorAll('.notification-checkbox:checked')];
                    currentForm.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
                    selectedCheckboxes.forEach(cb => {
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.name = 'notification_ids';
                        hiddenInput.value = cb.value;
                        currentForm.appendChild(hiddenInput);
                    });
                }
                currentForm.submit();
            }
            if (bsModal) bsModal.hide();
        });
    }

    
    const removeModalEl = document.getElementById('confirmRemoveFavoriteModal');
    const removeNameEl = document.getElementById('confirm-remove-favorite-name');
    const removeConfirmBtn = document.getElementById('confirmRemoveFavoriteBtn');
    let currentRemoveForm = null;
    const bsRemoveModal = removeModalEl && typeof bootstrap !== 'undefined' ? new bootstrap.Modal(removeModalEl) : null;

    document.querySelectorAll('form.remove-template').forEach(form => {
        form.addEventListener('submit', e => {
            e.preventDefault();
            currentRemoveForm = form;
            const name = form.dataset.itemName || 'this favorite';
            if (removeNameEl) removeNameEl.textContent = name;
            if (bsRemoveModal) bsRemoveModal.show();
            else if (confirm('Remove favorite ' + name + '?')) currentRemoveForm.submit();
        });
    });

    if (removeConfirmBtn) {
        removeConfirmBtn.addEventListener('click', () => {
            if (currentRemoveForm) currentRemoveForm.submit();
            if (bsRemoveModal) bsRemoveModal.hide();
        });
    }

    
    const decreaseBtn = document.getElementById('decrease-quantity');
    const increaseBtn = document.getElementById('increase-quantity');
    const quantityInput = document.getElementById('quantity-input');

    if (decreaseBtn && increaseBtn && quantityInput) {
        decreaseBtn.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value) || 1;
            if (currentValue > 1) quantityInput.value = currentValue - 1;
        });

        increaseBtn.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value) || 1;
            quantityInput.value = currentValue + 1;
        });
    }

    
    const selectAllCheckbox = document.getElementById('select-all');
    const mealCheckboxes = document.querySelectorAll('.meal-checkbox');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    const bulkDeleteForm = document.getElementById('bulk-delete-form');

    if (selectAllCheckbox && mealCheckboxes.length > 0 && bulkDeleteBtn) {
        selectAllCheckbox.addEventListener('change', () => {
            mealCheckboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
            toggleBulkDeleteBtn();
        });

        mealCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                selectAllCheckbox.checked = [...mealCheckboxes].every(cb => cb.checked);
                toggleBulkDeleteBtn();
            });
        });

        function toggleBulkDeleteBtn() {
            const anyChecked = [...mealCheckboxes].some(cb => cb.checked);
            bulkDeleteBtn.style.display = anyChecked ? 'inline-block' : 'none';
        }

        bulkDeleteBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const selectedCheckboxes = [...mealCheckboxes].filter(cb => cb.checked);
            const selectedCount = selectedCheckboxes.length;
            if (itemNameEl) itemNameEl.textContent = `${selectedCount} selected meal(s)`;
            if (bsModal) {
                currentForm = bulkDeleteForm;
                bsModal.show();
            } else if (confirm(`Delete ${selectedCount} selected meal(s)?`)) {
                bulkDeleteForm.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
                selectedCheckboxes.forEach(cb => {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'meal_ids';
                    hiddenInput.value = cb.value;
                    bulkDeleteForm.appendChild(hiddenInput);
                });
                bulkDeleteForm.submit();
            }
        });
    }

    
    const selectAllWorkoutsCheckbox = document.getElementById('select-all-workouts');
    const workoutCheckboxes = document.querySelectorAll('.workout-checkbox');
    const bulkDeleteWorkoutBtn = document.getElementById('bulk-delete-workout-btn');
    const bulkDeleteWorkoutForm = document.getElementById('bulk-delete-workout-form');

    if (selectAllWorkoutsCheckbox && workoutCheckboxes.length > 0 && bulkDeleteWorkoutBtn) {
        selectAllWorkoutsCheckbox.addEventListener('change', () => {
            workoutCheckboxes.forEach(cb => cb.checked = selectAllWorkoutsCheckbox.checked);
            toggleBulkDeleteWorkoutBtn();
        });

        workoutCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                selectAllWorkoutsCheckbox.checked = [...workoutCheckboxes].every(cb => cb.checked);
                toggleBulkDeleteWorkoutBtn();
            });
        });

        function toggleBulkDeleteWorkoutBtn() {
            const anyChecked = [...workoutCheckboxes].some(cb => cb.checked);
            bulkDeleteWorkoutBtn.style.display = anyChecked ? 'inline-block' : 'none';
        }

        bulkDeleteWorkoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const selectedCheckboxes = [...workoutCheckboxes].filter(cb => cb.checked);
            const selectedCount = selectedCheckboxes.length;
            if (itemNameEl) itemNameEl.textContent = `${selectedCount} selected workout(s)`;
            if (bsModal) {
                currentForm = bulkDeleteWorkoutForm;
                bsModal.show();
            } else if (confirm(`Delete ${selectedCount} selected workout(s)?`)) {
                bulkDeleteWorkoutForm.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
                selectedCheckboxes.forEach(cb => {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'workout_ids';
                    hiddenInput.value = cb.value;
                    bulkDeleteWorkoutForm.appendChild(hiddenInput);
                });
                bulkDeleteWorkoutForm.submit();
            }
        });
    }

    
    const selectAllNotificationsCheckbox = document.getElementById('select-all-notifications');
    const notificationCheckboxes = document.querySelectorAll('.notification-checkbox');
    const bulkDeleteNotificationBtn = document.getElementById('bulk-delete-notification-btn');
    const bulkDeleteNotificationForm = document.getElementById('bulk-delete-notification-form');

    if (selectAllNotificationsCheckbox && notificationCheckboxes.length > 0 && bulkDeleteNotificationBtn) {
        selectAllNotificationsCheckbox.addEventListener('change', () => {
            notificationCheckboxes.forEach(cb => cb.checked = selectAllNotificationsCheckbox.checked);
            toggleBulkDeleteNotificationBtn();
        });

        notificationCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                selectAllNotificationsCheckbox.checked = [...notificationCheckboxes].every(cb => cb.checked);
                toggleBulkDeleteNotificationBtn();
            });
        });

        function toggleBulkDeleteNotificationBtn() {
            const anyChecked = [...notificationCheckboxes].some(cb => cb.checked);
            bulkDeleteNotificationBtn.style.display = anyChecked ? 'inline-block' : 'none';
        }

        bulkDeleteNotificationBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const selectedCheckboxes = [...notificationCheckboxes].filter(cb => cb.checked);
            const selectedCount = selectedCheckboxes.length;
            if (itemNameEl) itemNameEl.textContent = `${selectedCount} selected notification(s)`;
            if (bsModal) {
                currentForm = bulkDeleteNotificationForm;
                bsModal.show();
            } else if (confirm(`Delete ${selectedCount} selected notification(s)?`)) {
                bulkDeleteNotificationForm.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
                selectedCheckboxes.forEach(cb => {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'notification_ids';
                    hiddenInput.value = cb.value;
                    bulkDeleteNotificationForm.appendChild(hiddenInput);
                });
                bulkDeleteNotificationForm.submit();
            }
        });
    }


    });
