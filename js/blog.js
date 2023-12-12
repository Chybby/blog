var markdownPreview = document.getElementById('markdown-preview');
var markdownEdit = document.getElementById('markdown-edit');

function updateMarkdownPreview() {
    markdownPreview.innerHTML = marked.parse(markdownEdit.value);
}

updateMarkdownPreview();

if (markdownEdit.addEventListener) {
    markdownEdit.addEventListener('input', function () {
        // event handling code for sane browsers
        updateMarkdownPreview();
    }, false);
} else if (markdownEdit.attachEvent) {
    markdownEdit.attachEvent('onpropertychange', function () {
        // IE-specific event handling code
        updateMarkdownPreview();
    });
}