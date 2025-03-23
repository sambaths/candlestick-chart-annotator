$(document).ready(function() {
    // Initialize Select2 for stock selection
    $('#stockSelect').select2({
        placeholder: 'Select stocks',
        multiple: true
    });

    // Initialize DataTable for stock summary
    const summaryTable = $('#summaryTable').DataTable({
        processing: true,
        serverSide: false,
        ajax: {
            url: '/api/stocks/summary',
            type: 'GET',
            error: function(xhr, error, thrown) {
                console.error('DataTables error:', error);
                $('#downloadStatus').removeClass().addClass('alert alert-danger')
                    .text('Error loading stock data: ' + error).show();
            }
        },
        columns: [
            { data: 'symbol' },
            { data: 'start_date' },
            { data: 'end_date' },
            { data: 'resolution' },
            { data: 'row_count' },
            {
                data: null,
                orderable: false,
                render: function(data, type, row) {
                    return '<button class="btn btn-danger btn-sm delete-btn" data-symbol="' + row.symbol + '">Delete</button>';
                }
            }
        ],
        order: [[0, 'asc']],
        pageLength: 25,
        language: {
            emptyTable: 'No stock data available',
            loadingRecords: 'Loading...',
            processing: 'Processing...',
            zeroRecords: 'No matching records found'
        },
        drawCallback: function(settings) {
            // Hide the status message if the table draws successfully
            $('#downloadStatus').hide();
        }
    });

    // Handle form submission for downloading data
    $('#downloadForm').on('submit', function(e) {
        e.preventDefault();
        
        const symbols = $('#stockSelect').val();
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        const resolution = $('#resolution').val();

        if (!symbols || symbols.length === 0) {
            alert('Please select at least one stock');
            return;
        }

        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }

        // Show progress bar and status
        $('#downloadProgress').show();
        $('#downloadStatus').removeClass().addClass('alert alert-info').text('Downloading data...').show();

        // Make API call to download data
        $.ajax({
            url: '/api/stocks/download',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                symbols: symbols,
                start_date: startDate,
                end_date: endDate,
                resolution: resolution
            }),
            success: function(response) {
                $('#downloadStatus').removeClass().addClass('alert alert-success').text(response.message);
                summaryTable.ajax.reload();
            },
            error: function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred';
                $('#downloadStatus').removeClass().addClass('alert alert-danger').text('Error: ' + error);
            },
            complete: function() {
                setTimeout(() => {
                    $('#downloadProgress').hide();
                }, 3000);
            }
        });
    });

    // Handle delete button clicks
    $('#summaryTable').on('click', '.delete-btn', function() {
        const symbol = $(this).data('symbol');
        console.log('Delete button clicked for symbol:', symbol);
        
        if (confirm(`Are you sure you want to delete data for ${symbol}?`)) {
            $('#downloadStatus').removeClass().addClass('alert alert-info').text('Deleting data...').show();
            console.log('Sending delete request for symbol:', symbol);
            
            $.ajax({
                url: `/api/data/delete/${symbol}`,
                method: 'DELETE',
                success: function(response) {
                    console.log('Delete success response:', response);
                    $('#downloadStatus').removeClass().addClass('alert alert-success').text(response.message).show();
                    // Reload the table with a slight delay to ensure the backend has processed the deletion
                    setTimeout(() => {
                        console.log('Reloading table data...');
                        summaryTable.ajax.reload(function(json) {
                            console.log('Table reload response:', json);
                        }, false);  // false means stay on current page
                    }, 500);
                },
                error: function(xhr, status, error) {
                    console.error('Delete error details:', {
                        status: status,
                        error: error,
                        response: xhr.responseText,
                        xhr: xhr
                    });
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred';
                    $('#downloadStatus').removeClass().addClass('alert alert-danger').text('Error: ' + errorMsg).show();
                }
            });
        } else {
            console.log('Delete cancelled by user for symbol:', symbol);
        }
    });

    // Initialize date pickers
    $('#startDate, #endDate').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true
    });

    // Set default dates
    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);

    $('#endDate').datepicker('setDate', today);
    $('#startDate').datepicker('setDate', lastMonth);
}); 