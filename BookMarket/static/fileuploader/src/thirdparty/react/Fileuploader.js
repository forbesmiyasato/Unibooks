import React, { Component, useEffect } from 'react';

const $ = window.jQuery;

class Fileuploader extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            name: "files",
            options: {}
        };
        
        if (props && Array.isArray(props)) {
            this.state.name = props[0];
            this.state.options = props[1];
        } else if (props && typeof props === 'object') {
            this.state.name = props.name;
            for (var key in props) {
                var val = props[key];
                
                if (typeof val != "string")
                    continue;
                if (['limit', 'maxSize', 'fileMaxSize', 'theme', 'listInput'].indexOf(key) > -1)
                    this.state.options[key] = val;
                if ('extensions' == key)
                    this.state.options[key] = val.replace(/ /g, '').split(',');
                if ('files' == key)
                    this.state.options[key] = JSON.parse(val);
            }
            if (props['disabled'])
                this.state.options['limit'] = 0;
        }
    }

    componentDidMount() {
        this.$el = $(this.el);
        this.$el.fileuploader($.extend(this.state.options, {
            enableApi: true
        }));
        this.api = $.fileuploader.getInstance(this.$el);
    };
    
    componentWillUnmount() {
        if (this.api)
            this.api.destroy();
    }

    render() {
        return (
            <input type="file" name={this.state.name} ref={el => this.el = el} />
        )
    }
}

export default Fileuploader;