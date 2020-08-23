'use strict';

// define domContainer
const domContainer = document.querySelector('#fileuploader-container');

// create Fileuploader element inline
ReactDOM.render(<Fileuploader name="files" limit="20" maxSize="20" extensions="jpg, jpeg, png" />, domContainer);

/*
// or
ReactDOM.render(React.createElement(Fileuploader, ["files", {
    // options will go here
}]), domContainer);
*/