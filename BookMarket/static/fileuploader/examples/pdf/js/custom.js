$(document).ready(function() {
	
	// enable fileuploader plugin
	$('input:file').fileuploader({
		limit: 1,
		extensions: ['pdf'],
		thumbnails: {
			pdf: {
				viewer: 'assets/pdf.js/web/viewer.html?file='
			},
		},
		onSelect: function(item) {
			item.popup.open();
		}
	});
	
});