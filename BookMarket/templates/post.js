    let class_select = document.getElementById('class_list');
    let department_select = document.getElementById('department_list')
    let department;

    // class_select.value = {{ item_class }}
    // department_select.value = {{ item_department }}
    class_select.setAttribute("disabled", "disabled");

    class_select.required = true;
    department_select.required = true;

    console.log(department_select)

    department_select.onchange = function () {
        var $select = $(document.getElementById('class_list'))
        var selectize = $select[0].selectize;
        department = department_select.value
        selectize.enable()
        selectize.clear();
        if (department) {
            fetch('/class/' + department).then(function (response) {
                response.json().then(function (data) {
                    let optionHTML = '';
                    selectize.clearOptions();
                    // optionHTML += '<option data-display="Select Class">Select</option>'
                    for (let item_class of data.classes) {
                        // optionHTML += `<option value="${item_class.id}">${item_class.class_name}</option>`;
                        selectize.addOption({ value: item_class.id, text: item_class.class_name });
                        selectize.refreshOptions()
                    }
                    class_select.innerHTML = optionHTML;
                    // class_select.removeAttribute("disabled");
                }).then(function () {
                    {% if item_class is defined %}
                    if ('{{ item_class.id }}') {
                        console.log("!!!")
                        selectize.setValue('{{item_class.id}}')
                        selectize.refreshItems()
                        selectize.close()
                    }
                    {% endif %}
                })
            });
        } else {
            selectize.disable()
        }

        let department_input = document.getElementById('department_list-selectized');

        department_input.setCustomValidity('')

        console.log(!department_input.checkValidity())
        if (!department_input.checkValidity()) {
            department_input.setCustomValidity("Please Select Department")
        } else {
            department_input.setCustomValidity('')
        }
    }

    class_select.onchange = function () {
        let class_input = document.getElementById('class_list-selectized');

        class_input.setCustomValidity('')

        console.log(!class_input.checkValidity())
        if (!class_input.checkValidity()) {
            class_input.setCustomValidity("Please Select Course")
        } else {
            class_input.setCustomValidity('')
        }
    }

    $(document).ready(function () {
        $('select').selectize({
            sortField: 'text'
        });

        let department_input = document.getElementById('department_list-selectized');
        let class_input = document.getElementById('class_list-selectized');
        if (department_input) { department_input.setCustomValidity("Please Select Department") }
        if (class_input) { class_input.setCustomValidity("Please Select Course") }
        department_input.value = '{{department|safe}}'
        {% if item_class is defined %}
        class_input.value = '{{item_class.class_name|safe}}'
        {% endif %}

        // enable fileuploader plugin
        $('input[name="files"]').fileuploader({
            extensions: null,
            changeInput: ' ',
            theme: 'thumbnails',
            enableApi: true,
            addMore: true,
            limit: 8,
            extensions: ['jpg', 'png', 'jpeg'],
            {% if item and(images | length > 0) %}
            files: [
        {% for image in images %}
    {
        "name": "{{image.image_name}}",
            "file": "https://book-advertisement-site.s3-us-west-2.amazonaws.com/{{image.image_file}}",
                "type": "image/",
                    "size": '{{image.image_size}}',
                        "data": {
            "thumbnail": "https://book-advertisement-site.s3-us-west-2.amazonaws.com/{{image.image_file}}",
        }
    },
    {% endfor %}
        ],
    {% endif %}
    thumbnails: {
        box: '<div class="fileuploader-items">' +
            '<ul class="fileuploader-items-list">' +
            '<li class="fileuploader-thumbnails-input"><div class="fileuploader-thumbnails-input-inner"><i>+</i></div></li>' +
            '</ul>' +
            '</div>',
            item: '<li class="fileuploader-item">' +
                '<div class="fileuploader-item-inner">' +
                '<div class="type-holder">${extension}</div>' +
                '<div class="actions-holder">' +
                '<button type="button" class="fileuploader-action fileuploader-action-remove" title="${captions.remove}"><i class="fileuploader-icon-remove"></i></button>' +
                '</div>' +
                '<div class="thumbnail-holder">' +
                '${image}' +
                '<span class="fileuploader-action-popup"></span>' +
                '</div>' +
                '<div class="content-holder"><h5>${name}</h5><span>${size2}</span></div>' +
                '<div class="progress-holder">${progressBar}</div>' +
                '</div>' +
                '</li>',
                item2: '<li class="fileuploader-item">' +
                    '<div class="fileuploader-item-inner">' +
                    '<div class="type-holder">${extension}</div>' +
                    '<div class="actions-holder">' +
                    '<a href="${file}" class="fileuploader-action fileuploader-action-download" title="${captions.download}" download><i class="fileuploader-icon-download"></i></a>' +
                    '<button type="button" class="fileuploader-action fileuploader-action-remove" title="${captions.remove}"><i class="fileuploader-icon-remove"></i></button>' +
                    '</div>' +
                    '<div class="thumbnail-holder">' +
                    '${image}' +
                    '<span class="fileuploader-action-popup"></span>' +
                    '</div>' +
                    '<div class="content-holder"><h5 title="${name}">${name}</h5><span>${size2}</span></div>' +
                    '<div class="progress-holder">${progressBar}</div>' +
                    '</div>' +
                    '</li>',
                    startImageRenderer: true,
                        canvasImage: false,
                            _selectors: {
            list: '.fileuploader-items-list',
                item: '.fileuploader-item',
                    start: '.fileuploader-action-start',
                        retry: '.fileuploader-action-retry',
                            remove: '.fileuploader-action-remove'
        },
        onItemShow: function (item, listEl, parentEl, newInputEl, inputEl) {
            var plusInput = listEl.find('.fileuploader-thumbnails-input'),
                api = $.fileuploader.getInstance(inputEl.get(0));

            plusInput.insertAfter(item.html)[api.getOptions().limit && api.getChoosedFiles().length >= api.getOptions().limit ? 'hide' : 'show']();

            if (item.format == 'image') {
                item.html.find('.fileuploader-item-icon').hide();
            }
        },
        onItemRemove: function (html, listEl, parentEl, newInputEl, inputEl) {
            var plusInput = listEl.find('.fileuploader-thumbnails-input'),
                api = $.fileuploader.getInstance(inputEl.get(0));
            console.log(inputEl)
            html.children().animate({ 'opacity': 0 }, 200, function () {
                html.remove();

                if (api.getOptions().limit && api.getChoosedFiles().length - 1 < api.getOptions().limit)
                    plusInput.show();
            });

            deleted = true;
        }
    },
    dragDrop: {
        container: '.fileuploader-thumbnails-input'
    },
    afterRender: function (listEl, parentEl, newInputEl, inputEl) {
        var plusInput = listEl.find('.fileuploader-thumbnails-input'),
            api = $.fileuploader.getInstance(inputEl.get(0));

        plusInput.on('click', function () {
            api.open();
        });

        api.getOptions().dragDrop.container = plusInput;
    },
        });


    var $form = $('#post-form');

    // form submit
    $form.on('submit', function (e) {
        e.preventDefault();

        var formData = new FormData(),
            _fileuploaderFields = [];

        // append inputs to FormData
        $.each($form.serializeArray(), function (key, field) {
            console.log(field.name, field.value)
            formData.append(field.name, field.value);
        });

        input = document.querySelector('input[name="files[]"')

        // append file inputs to FormData
        var $input = $(input),
            name = $input.attr('name'),
            files = $input.prop('files'),
            api = $.fileuploader.getInstance($input);

        // add fileuploader files to the formdata
        if (api) {
            if ($.inArray(name, _fileuploaderFields) > -1)
                return;
            files = api.getChoosedFiles();
            _fileuploaderFields.push($input);
        }

        console.log(files);
        for (var i = 0; i < files.length; i++) {
            formData.append(name, (files[i].file ? files[i].file : files[i]), (files[i].name ? files[i].name : false));
        }

        console.log("???", formData.get("fileuploader-list-files").split("\""))
        let fileArray = formData.get("fileuploader-list-files").split("\"");

        var blob = null;

        let remainingFiles = []

        for (var i = 3; i < fileArray.length; i += 4) {
            // console.log(fileArray[i])
            // console.log(fileArray[i]);
            // let file = new File([fileArray[i]], "test." + type, {type: "image/" + type})
            if (fileArray[i].startsWith("https://")) {
                let type = fileArray[i].split('.').pop()
                let image_name = fileArray[i].split('/').pop()
                console.log(image_name)
                console.log(type);
                remainingFiles.push(image_name);
            }
        }

        formData.append('remaining_files', remainingFiles);
        // Display the values
        for (var value of formData.values()) {
            console.log("1", value);
        }

        post_url = '{{legend}}' === "New" ? "{{url_for('new_item')}}" : '{{item}}' ? "{{url_for('shop_api.item', item_id=item_id)}}" : null
        $.ajax({
            url: post_url || '#',
            data: formData,
            type: $form.attr('method') || 'POST',
            enctype: $form.attr('enctype') || 'multipart/form-data',
            cache: false,
            contentType: false,
            processData: false,
            success: function (data) {
                console.log("success")
                window.location.href = data['url']
            },
            beforeSend: function () {
                $('#form-spinner').modal({ backdrop: 'static', keyboard: false })
                $('#editModal').modal({ backdrop: 'static', keyboard: false })
                $('#form-spinner').modal('show')
                $('#editModal').html(`<div class="modal-dialog modal-sm modal-dialog-centered" role="document">
        <div class="modal-content bg-light">
            <div class="modal-body">
                <div class="spinner-border mr-3" style="float: left; width: 3rem; height: 3rem;" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <h5>Just one second</h5>
                <span class="mb-0">We're posting the item for you.</span>
            </div>
        </div>
    </div>`)
            },
            complete: function () {

            }
        });


        $('form').submit(function () {
            $(this).find(':submit').attr('disabled', 'disabled');
        });
    });
    });