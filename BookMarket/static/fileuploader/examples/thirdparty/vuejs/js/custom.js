new Vue({
    el: '#app',
    methods: {
        getFileuploaderOptions(cmp) {
            cmp.options.limit = 20;
        }
    }
});