# Print & Export Functionality Guide

This guide explains how to use the comprehensive print and export functionality available throughout the School Management System.

## Features

The print/export system supports:
- ✅ **Print to PDF** - High-quality PDF generation
- ✅ **Print to Image** - PNG image export
- ✅ **Export to PDF** - Direct PDF download
- ✅ **Export to Excel** - For tables (XLSX format)
- ✅ **Export to CSV** - For tables (CSV format)
- ✅ **Export to Word** - RTF format (compatible with Microsoft Word)
- ✅ **Browser Print** - Standard browser print dialog

## Quick Usage

### Method 1: Using the Export Menu (Recommended)

```html
<button onclick="showExportMenu('.card', {filename: 'my_document'}); return false;">
    <i class="fas fa-download"></i> Export Options
</button>
```

This opens a modal with all export options.

### Method 2: Direct Function Calls

```javascript
// Print to PDF
exportToPDF('.card', {filename: 'my_document'});

// Export as Image
printToImage('.card', {filename: 'my_document'});

// Export table to Excel
exportToExcel('#myTable', {filename: 'my_data'});

// Export table to CSV
exportToCSV('#myTable', {filename: 'my_data'});

// Export to Word (RTF)
exportToWord('.card', {filename: 'my_document'});

// Standard print
printDocument('.card');
```

### Method 3: Using the Reusable Component

Include the print/export button component in your template:

```django
{% include 'includes/print_export_button.html' with selector='.card' filename='document_name' %}
```

**Parameters:**
- `selector`: CSS selector for element to print/export (default: 'body')
- `filename`: Base filename without extension (optional)
- `button_class`: Additional CSS classes (optional)
- `button_text`: Button text (optional)
- `show_dropdown`: Show dropdown menu (default: True)
- `table_selector`: For Excel/CSV export (optional)

## Examples

### Example 1: Simple Print Button

```html
<button onclick="printDocument('.my-content');">
    <i class="fas fa-print"></i> Print
</button>
```

### Example 2: Print Button with Export Dropdown

```html
<div class="btn-group">
    <button onclick="printDocument('.my-content');" class="btn btn-primary">
        <i class="fas fa-print"></i> Print
    </button>
    <button class="btn btn-primary dropdown-toggle" data-toggle="dropdown">
        <span class="sr-only">Toggle Dropdown</span>
    </button>
    <div class="dropdown-menu dropdown-menu-right">
        <a class="dropdown-item" href="#" onclick="showExportMenu('.my-content', {filename: 'document'}); return false;">
            <i class="fas fa-download"></i> All Export Options
        </a>
        <div class="dropdown-divider"></div>
        <a class="dropdown-item" href="#" onclick="exportToPDF('.my-content', {filename: 'document'}); return false;">
            <i class="fas fa-file-pdf text-danger"></i> Export to PDF
        </a>
        <a class="dropdown-item" href="#" onclick="printToImage('.my-content', {filename: 'document'}); return false;">
            <i class="fas fa-image text-info"></i> Export as Image
        </a>
    </div>
</div>
```

### Example 3: Table Export

```html
<table id="myTable">
    <!-- table content -->
</table>

<button onclick="exportToExcel('#myTable', {filename: 'table_data'});">
    <i class="fas fa-file-excel"></i> Export to Excel
</button>

<button onclick="exportToCSV('#myTable', {filename: 'table_data'});">
    <i class="fas fa-file-csv"></i> Export to CSV
</button>
```

## Selector Tips

- Use specific selectors to print only relevant content
- Example: `.card` prints only the card, not the entire page
- Example: `#admissionsTable` prints only the table
- Use `.no-print` class to hide elements during print

## CSS for Print Styling

Add print-specific styles:

```css
@media print {
    .no-print {
        display: none !important;
    }
    
    .btn, button {
        display: none !important;
    }
    
    @page {
        margin: 1cm;
    }
}
```

## Updated Templates

The following templates have been updated with the new print/export functionality:

1. ✅ `students/manage_admissions.html`
2. ✅ `students/admission_details.html`
3. ✅ `students/student_details.html`
4. ✅ `teachers/report_card.html`
5. ✅ `finances/fees/fee_detail.html`
6. ✅ `finances/expense_detail.html`

## Adding Print/Export to Other Templates

To add print/export functionality to any template:

1. **Simple approach**: Replace `onclick="window.print()"` with:
   ```html
   onclick="showExportMenu('.your-selector', {filename: 'your_filename'}); return false;"
   ```

2. **Using the component**:
   ```django
   {% include 'includes/print_export_button.html' with selector='.your-selector' filename='your_filename' %}
   ```

3. **Custom implementation**: Use the JavaScript functions directly:
   ```javascript
   exportToPDF('.your-selector', {filename: 'your_filename'});
   ```

## Troubleshooting

### Libraries not loading
- Check internet connection (CDN libraries are loaded from CDN)
- Libraries load automatically when needed
- Wait a few seconds after page load before using export functions

### PDF generation issues
- Ensure the element exists before calling export functions
- Check browser console for errors
- Try a different selector if one doesn't work

### Excel/CSV export
- Only works with `<table>` elements
- Ensure table has proper structure
- Use table selector: `#tableId` or `.table-class`

## Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ Internet Explorer (limited support)

## Performance Notes

- PDF generation may take a few seconds for large documents
- Image export scales content for better quality
- Excel/CSV export is fast for tables
- Loading indicator shows during processing

## Support

For issues or questions, check:
1. Browser console for JavaScript errors
2. Network tab for failed CDN requests
3. Ensure `print-export.js` is loaded (check in Network tab)
