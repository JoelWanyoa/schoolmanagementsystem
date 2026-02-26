/**
 * Print & Export Utility
 * Provides comprehensive print and export functionality for all pages
 * Supports: PDF, Image, Word, Excel, CSV formats
 */

class PrintExportManager {
    constructor() {
        this.loadLibraries();
    }

    /**
     * Dynamically load required libraries
     */
    loadLibraries() {
        // Load html2pdf.js for PDF generation
        if (!window.html2pdf) {
            const script1 = document.createElement('script');
            script1.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
            script1.onload = () => console.log('html2pdf loaded');
            document.head.appendChild(script1);
        }

        // Load html2canvas for image generation
        if (!window.html2canvas) {
            const script2 = document.createElement('script');
            script2.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            script2.onload = () => console.log('html2canvas loaded');
            document.head.appendChild(script2);
        }

        // Load SheetJS (xlsx) for Excel export
        if (!window.XLSX) {
            const script3 = document.createElement('script');
            script3.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
            script3.onload = () => console.log('XLSX loaded');
            document.head.appendChild(script3);
        }

        // Note: docx library is complex and requires additional setup
        // For now, Word export uses a simpler text-based approach
        // Full docx support can be added later if needed
    }

    /**
     * Get the element to print/export
     * @param {string|HTMLElement} selector - CSS selector or element
     * @returns {HTMLElement}
     */
    getElement(selector) {
        if (typeof selector === 'string') {
            const element = document.querySelector(selector);
            if (!element) {
                throw new Error(`Element not found: ${selector}`);
            }
            return element;
        }
        return selector;
    }

    /**
     * Get filename from page title or custom name
     * @param {string} format - File format (pdf, png, docx, xlsx, csv)
     * @param {string} customName - Custom filename
     * @returns {string}
     */
    getFilename(format, customName = null) {
        if (customName) {
            return `${customName}.${format}`;
        }
        const title = document.title || 'document';
        const cleanTitle = title.replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        return `${cleanTitle}_${timestamp}.${format}`;
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        const loading = document.createElement('div');
        loading.id = 'print-export-loading';
        loading.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.5); z-index: 99999; display: flex; 
                        align-items: center; justify-content: center;">
                <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-3 mb-0">Processing...</p>
                </div>
            </div>
        `;
        document.body.appendChild(loading);
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loading = document.getElementById('print-export-loading');
        if (loading) {
            loading.remove();
        }
    }

    /**
     * Print to PDF
     * @param {string|HTMLElement} selector - Element to print
     * @param {object} options - html2pdf options
     */
    async printToPDF(selector = 'body', options = {}) {
        this.showLoading();
        try {
            const element = this.getElement(selector);
            const defaultOptions = {
                margin: [10, 10, 10, 10],
                filename: this.getFilename('pdf', options.filename),
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { 
                    scale: 2,
                    useCORS: true,
                    logging: false
                },
                jsPDF: { 
                    unit: 'mm', 
                    format: 'a4', 
                    orientation: 'portrait' 
                },
                ...options
            };

            // Wait for html2pdf to be available
            await this.waitForLibrary('html2pdf', 5000);

            await html2pdf().set(defaultOptions).from(element).save();
            this.showToast('PDF generated successfully!', 'success');
        } catch (error) {
            console.error('PDF generation error:', error);
            this.showToast('Error generating PDF: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Export to PDF (same as print but with different options)
     */
    async exportToPDF(selector = 'body', options = {}) {
        await this.printToPDF(selector, { ...options, filename: options.filename || this.getFilename('pdf') });
    }

    /**
     * Print to Image (PNG)
     * @param {string|HTMLElement} selector - Element to capture
     * @param {object} options - html2canvas options
     */
    async printToImage(selector = 'body', options = {}) {
        this.showLoading();
        try {
            const element = this.getElement(selector);
            
            // Wait for html2canvas to be available
            await this.waitForLibrary('html2canvas', 5000);

            const canvas = await html2canvas(element, {
                scale: 2,
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff',
                ...options
            });

            // Convert to image and download
            canvas.toBlob((blob) => {
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = this.getFilename('png', options.filename);
                link.click();
                URL.revokeObjectURL(url);
                this.showToast('Image exported successfully!', 'success');
            }, 'image/png');
        } catch (error) {
            console.error('Image generation error:', error);
            this.showToast('Error generating image: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Export table data to Excel
     * @param {string|HTMLElement} tableSelector - Table element or selector
     * @param {object} options - Export options
     */
    async exportToExcel(tableSelector, options = {}) {
        this.showLoading();
        try {
            const table = this.getElement(tableSelector);
            
            // Wait for XLSX library
            await this.waitForLibrary('XLSX', 5000);

            // Extract table data
            const wb = XLSX.utils.book_new();
            const ws = XLSX.utils.table_to_sheet(table);
            XLSX.utils.book_append_sheet(wb, ws, options.sheetName || 'Sheet1');

            // Generate Excel file
            XLSX.writeFile(wb, this.getFilename('xlsx', options.filename));
            this.showToast('Excel file exported successfully!', 'success');
        } catch (error) {
            console.error('Excel export error:', error);
            this.showToast('Error exporting to Excel: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Export table data to CSV
     * @param {string|HTMLElement} tableSelector - Table element or selector
     * @param {object} options - Export options
     */
    async exportToCSV(tableSelector, options = {}) {
        this.showLoading();
        try {
            const table = this.getElement(tableSelector);
            
            // Wait for XLSX library (it can also generate CSV)
            await this.waitForLibrary('XLSX', 5000);

            const ws = XLSX.utils.table_to_sheet(table);
            const csv = XLSX.utils.sheet_to_csv(ws);

            // Download CSV
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.download = this.getFilename('csv', options.filename);
            link.click();
            URL.revokeObjectURL(url);
            this.showToast('CSV file exported successfully!', 'success');
        } catch (error) {
            console.error('CSV export error:', error);
            this.showToast('Error exporting to CSV: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Export to Word document (RTF format for compatibility)
     * @param {string|HTMLElement} selector - Element to export
     * @param {object} options - Export options
     */
    async exportToWord(selector = 'body', options = {}) {
        this.showLoading();
        try {
            const element = this.getElement(selector);
            
            // Extract text content and structure
            const text = element.innerText || element.textContent;
            const title = document.title || 'Document';
            
            // Create RTF content (Rich Text Format - compatible with Word)
            const rtfContent = `{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}
{\\colortbl ;\\red0\\green0\\blue0;}
\\f0\\fs24 {\\b ${title}}\\par\\par
${text.replace(/\n/g, '\\par ')}
}`;

            // Create blob and download
            const blob = new Blob([rtfContent], { type: 'application/rtf' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = this.getFilename('rtf', options.filename);
            link.click();
            URL.revokeObjectURL(url);
            this.showToast('Word document (RTF) exported successfully!', 'success');
        } catch (error) {
            console.error('Word export error:', error);
            this.showToast('Error exporting to Word: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Standard browser print
     * @param {string|HTMLElement} selector - Element to print (optional, defaults to window.print)
     */
    print(selector = null) {
        if (selector) {
            // Create a new window with the content
            const element = this.getElement(selector);
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                    <head>
                        <title>${document.title}</title>
                        <style>
                            ${this.getPrintStyles()}
                        </style>
                    </head>
                    <body>
                        ${element.innerHTML}
                    </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.focus();
            setTimeout(() => {
                printWindow.print();
                printWindow.close();
            }, 250);
        } else {
            window.print();
        }
    }

    /**
     * Get print-specific CSS styles
     */
    getPrintStyles() {
        return `
            @media print {
                @page { margin: 1cm; }
                body { font-family: Arial, sans-serif; }
                .no-print { display: none !important; }
                .btn, button { display: none !important; }
                a[href]:after { content: ""; }
            }
        `;
    }

    /**
     * Wait for a library to be available
     * @param {string} libName - Library name (html2pdf, html2canvas, XLSX, docx)
     * @param {number} timeout - Timeout in ms
     */
    waitForLibrary(libName, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const checkLibrary = () => {
                let available = false;
                switch(libName) {
                    case 'html2pdf':
                        available = typeof window.html2pdf !== 'undefined';
                        break;
                    case 'html2canvas':
                        available = typeof window.html2canvas !== 'undefined';
                        break;
                    case 'XLSX':
                        available = typeof window.XLSX !== 'undefined';
                        break;
                    case 'docx':
                        available = typeof window.docx !== 'undefined';
                        break;
                }

                if (available) {
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    reject(new Error(`Library ${libName} failed to load within ${timeout}ms`));
                } else {
                    setTimeout(checkLibrary, 100);
                }
            };
            checkLibrary();
        });
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        if (window.toastManager) {
            window.toastManager.showToast(message, type);
        } else {
            alert(message);
        }
    }

    /**
     * Show export menu modal
     * @param {string|HTMLElement} selector - Element to export
     * @param {object} options - Options
     */
    showExportMenu(selector, options = {}) {
        const element = this.getElement(selector);
        const modalId = 'exportMenuModal';
        
        // Remove existing modal if any
        const existingModal = document.getElementById(modalId);
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-download"></i> Export Options
                        </h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-6 mb-3">
                                <button class="btn btn-danger btn-block export-btn" data-format="pdf">
                                    <i class="fas fa-file-pdf"></i><br>
                                    <small>PDF</small>
                                </button>
                            </div>
                            <div class="col-6 mb-3">
                                <button class="btn btn-info btn-block export-btn" data-format="image">
                                    <i class="fas fa-image"></i><br>
                                    <small>Image (PNG)</small>
                                </button>
                            </div>
                            <div class="col-6 mb-3">
                                <button class="btn btn-success btn-block export-btn" data-format="excel">
                                    <i class="fas fa-file-excel"></i><br>
                                    <small>Excel</small>
                                </button>
                            </div>
                            <div class="col-6 mb-3">
                                <button class="btn btn-primary btn-block export-btn" data-format="word">
                                    <i class="fas fa-file-word"></i><br>
                                    <small>Word (RTF)</small>
                                </button>
                            </div>
                            <div class="col-6 mb-3">
                                <button class="btn btn-secondary btn-block export-btn" data-format="csv">
                                    <i class="fas fa-file-csv"></i><br>
                                    <small>CSV</small>
                                </button>
                            </div>
                            <div class="col-6 mb-3">
                                <button class="btn btn-warning btn-block export-btn" data-format="print">
                                    <i class="fas fa-print"></i><br>
                                    <small>Print</small>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        $(modal).modal('show');

        // Handle export button clicks
        modal.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const format = e.currentTarget.dataset.format;
                $(modal).modal('hide');
                
                switch(format) {
                    case 'pdf':
                        await this.exportToPDF(selector, options);
                        break;
                    case 'image':
                        await this.printToImage(selector, options);
                        break;
                    case 'excel':
                        await this.exportToExcel(selector, options);
                        break;
                    case 'word':
                    case 'rtf':
                        await this.exportToWord(selector, options);
                        break;
                    case 'csv':
                        await this.exportToCSV(selector, options);
                        break;
                    case 'print':
                        this.print(selector);
                        break;
                }
            });
        });

        // Remove modal on close
        $(modal).on('hidden.bs.modal', () => {
            modal.remove();
        });
    }
}

// Initialize global instance
window.printExportManager = new PrintExportManager();

// Helper functions for easy access
window.printToPDF = (selector, options) => window.printExportManager.printToPDF(selector, options);
window.printToImage = (selector, options) => window.printExportManager.printToImage(selector, options);
window.exportToPDF = (selector, options) => window.printExportManager.exportToPDF(selector, options);
window.exportToExcel = (selector, options) => window.printExportManager.exportToExcel(selector, options);
window.exportToCSV = (selector, options) => window.printExportManager.exportToCSV(selector, options);
window.exportToWord = (selector, options) => window.printExportManager.exportToWord(selector, options);
window.showExportMenu = (selector, options) => window.printExportManager.showExportMenu(selector, options);
window.printDocument = (selector) => window.printExportManager.print(selector);
