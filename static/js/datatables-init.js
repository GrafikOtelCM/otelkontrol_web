$(document).ready(function () {
  $('#reportTable').DataTable({
    dom: 'Bfrtip',
    buttons: [
      {
        extend: 'copy',
        text: '📋 Kopyala',
        className: 'btn btn-outline-primary'
      },
      {
        extend: 'excel',
        text: '📥 Excel',
        className: 'btn btn-outline-success'
      },
      {
        extend: 'pdf',
        text: '📄 PDF',
        className: 'btn btn-outline-danger'
      },
      {
        extend: 'print',
        text: '🖨️ Yazdır',
        className: 'btn btn-outline-secondary'
      }
    ],
    language: {
      url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/tr.json'
    },
    responsive: true,
    pageLength: 25,
    lengthMenu: [10, 25, 50, 100],
    columnDefs: [
      { targets: '_all', className: 'align-middle' }
    ]
  });
});
