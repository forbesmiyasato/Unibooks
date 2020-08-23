<template>
    <input type="file" :name="name">
</template>

<script>
    const jQuery = window.jQuery;

    export default {
        name: 'Fileuploader',
        props: ['name'],
        created() {
            this.options = {};
            this.$emit('options', this);
            if (!this.options)
                this.options = {};

            for (var key in this.$attrs) {
                var val = this.$attrs[key];

                if (typeof val != "string")
                    continue;

                if (['limit', 'maxSize', 'fileMaxSize', 'theme', 'listInput'].indexOf(key) > -1)
                    this.options[key] = val;
                if ('extensions' == key)
                    this.options[key] = val.replace(/ /g, '').split(',');
                if ('files' == key)
                    this.options[key] = JSON.parse(val);

                if (typeof this.options[key] != "undefined")
                    this.$attrs[key] = null;
            }

            if (this.options['disabled'])
                this.options['limit'] = 0;

            this.$emit('created', this);
        },
        mounted() {
            this.el = jQuery(this.$el);
            this.el.fileuploader(jQuery.extend(this.options, {
                enableApi: true
            }));
            this.api = jQuery.fileuploader.getInstance(this.el);

            this.$emit('mounted', this);
        },
        beforeDestroy() {
            if (this.api)
                this.api.destroy();

            this.$emit('destroyed', this);
        }
    }
</script>

<style>

</style>