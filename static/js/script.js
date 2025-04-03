// Form validation
function validateForm() {
    let isValid = true;
    
    // Validate first name
    const firstNameInput = document.getElementById('first_name');
    if (!firstNameInput.value.trim()) {
        displayError(firstNameInput, 'Please enter a first name.');
        isValid = false;
    } else {
        firstNameInput.classList.remove('is-invalid');
        firstNameInput.classList.add('is-valid');
    }
    
    // Validate last name
    const lastNameInput = document.getElementById('last_name');
    if (!lastNameInput.value.trim()) {
        displayError(lastNameInput, 'Please enter a last name.');
        isValid = false;
    } else {
        lastNameInput.classList.remove('is-invalid');
        lastNameInput.classList.add('is-valid');
    }
    
    // Validate telephone
    const telephoneInput = document.getElementById('telephone');
    if (!telephoneInput.value.trim() || !validatePhone(telephoneInput.value)) {
        displayError(telephoneInput, 'Please enter a valid telephone number.');
        isValid = false;
    } else {
        telephoneInput.classList.remove('is-invalid');
        telephoneInput.classList.add('is-valid');
    }
    
    // Validate email
    const emailInput = document.getElementById('email');
    if (!emailInput.value.trim() || !validateEmail(emailInput.value)) {
        displayError(emailInput, 'Please enter a valid email address.');
        isValid = false;
    } else {
        emailInput.classList.remove('is-invalid');
        emailInput.classList.add('is-valid');
    }
    
    // Validate house selection
    const houseSelected = document.querySelector('input[name="house_number"]:checked');
    if (!houseSelected) {
        document.getElementById('house1').parentElement.parentElement.parentElement.classList.add('was-validated');
        isValid = false;
    }
    
    // Validate booking sites (at least one must be selected)
    const bookingSitesSelected = document.querySelectorAll('input[name="booking_sites"]:checked');
    if (bookingSitesSelected.length === 0) {
        document.getElementById('booking-sites-feedback').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('booking-sites-feedback').style.display = 'none';
    }
    
    return isValid;
}

function displayError(element, message) {
    element.classList.remove('is-valid');
    element.classList.add('is-invalid');
    
    // Find and update the invalid feedback message
    const feedbackElement = element.nextElementSibling;
    if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
        feedbackElement.textContent = message;
    }
}

function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function validatePhone(phone) {
    // Basic phone validation - can be customized based on your requirements
    const re = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/;
    return re.test(String(phone));
}

// Initialize DataTable for travelers
function initializeDataTable() {
    fetch('/get_travelers')
        .then(response => response.json())
        .then(data => {
            const table = $('#travelersTable').DataTable({
                data: data,
                columns: [
                    { data: 'id' },
                    { data: 'first_name' },
                    { data: 'last_name' },
                    { data: 'telephone' },
                    { data: 'email' },
                    { 
                        data: 'house_number',
                        render: function(data) {
                            return `House ${data}`;
                        }
                    },
                    { data: 'booking_sites' },
                    { data: 'registration_date' }
                ],
                order: [[0, 'desc']],
                responsive: true,
                language: {
                    emptyTable: "No travelers registered yet"
                },
                dom: 'Bfrtip',
                buttons: [
                    {
                        text: '<i class="fas fa-sync-alt"></i> Refresh',
                        className: 'btn btn-sm btn-secondary',
                        action: function (e, dt, node, config) {
                            dt.clear().draw();
                            fetch('/get_travelers')
                                .then(response => response.json())
                                .then(data => {
                                    dt.rows.add(data).draw();
                                })
                                .catch(error => console.error('Error refreshing data:', error));
                        }
                    }
                ]
            });
        })
        .catch(error => console.error('Error loading travelers:', error));
}

// Export to Excel function
function exportToExcel() {
    fetch('/get_travelers')
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                alert('No data to export');
                return;
            }
            
            const worksheet = XLSX.utils.json_to_sheet(data);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Travelers');
            
            // Generate Excel file
            const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
            saveAsExcelFile(excelBuffer, 'travelers_data');
        })
        .catch(error => console.error('Error exporting data:', error));
}

function saveAsExcelFile(buffer, fileName) {
    const data = new Blob([buffer], { type: 'application/octet-stream' });
    saveAs(data, fileName + '.xlsx');
}

// Set up offline indicator
document.addEventListener('DOMContentLoaded', function() {
    const statusIndicator = document.getElementById('status-indicator');
    const connectionStatus = document.getElementById('connection-status');
    
    // Set to "Local Mode" by default
    statusIndicator.classList.add('status-online');
    connectionStatus.textContent = 'Local Mode';
});

// Refresh backup list
function createBackup() {
    window.location.href = '/backup_database';
}