function getParameterByName(name) {
    var match = RegExp("[?&]" + name + "=([^&]*)").exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}

const showSwitch = (show_term) => {
    switch (show_term) {
        case "all":
            $("#show-button-text").html("Showing All");
            $("#all").html("Show Less");
            break;
        default:
            $("#show-button-text").html("Show All");
            $("#all").html("Show All");
            break;
    }
};
const filterSwitch = (filter_term) => {
    switch (filter_term) {
        case "0+25":
            $("#filter-button-text").html("Filter By: $0 - $25");
            break;
        case "25+50":
            $("#filter-button-text").html("Filter By: $25 - $50");
            break;
        case "50+100":
            $("#filter-button-text").html("Filter By: $50 - $100");
            break;
        case "100+150":
            $("#filter-button-text").html("Filter By: $100 - $150");
            break;
        case "150+99999":
            $("#filter-button-text").html("Filter By: Over $150");
            break;
        default:
            $("#filter-button-text").html("Filter By");
            break;
    }
};
const sortSwitch = (sort_term) => {
    switch (sort_term) {
        case "newest":
            $("#sort-button-text").html("Sort By: Newest-Oldest");
            break;
        case "oldest":
            $("#sort-button-text").html("Sort By: Oldest-Newest");
            break;
        case "lowest":
            $("#sort-button-text").html("Sort By: Price: Low-High");
            break;
        case "highest":
            $("#sort-button-text").html("Sort By: Price: High-Low");
            break;
        default:
            $("#sort-button-text").html("Sort By");
            break;
    }
};

var getDataRequest = false;
const getData = (url, first) => {
    if (!getDataRequest) {
        getDataRequest = true;

        $.ajax({
            url: url,
            type: "get",
            data: null,
            async: true,
            success: function (response) {
                if (response.error) {
                    if (response.error === "no school in session") {
                        location.reload();
                    }
                }
                let course = response.course;
                let department = response.department;
                let search = response.search;
                let numResults = response.numResults;
                let category = response.category;

                if (course) {
                    $("#nav-header").html(course.long);
                    $("#nav-department").html(
                        '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                            `<a onclick="return filterByDepartment(${department.id})" href="/shop?department=${department.id}">${department.short}</a>`
                    );
                    $("#nav-course").html(
                        '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                            `<a class="text-white">${course.short}</a>`
                    );
                } else if (department) {
                    $("#nav-header").html(department.long);
                    $("#nav-department").html(
                        '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                            `<a class="text-white">${department.short}</a>`
                    );
                    $("#nav-course").html("");
                } else if (search) {
                    $("#nav-header").html(
                        `${numResults} results found for "${search}"`
                    );
                    $("#nav-department").html(
                        '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                            `<a class="text-white">"${search}"</a>`
                    );
                    $("#nav-course").html("");
                } else if (category) {
                    if (category.long === "All Non-Textbooks") {
                        $("#nav-header").html(category.long);
                        $("#nav-department").html(
                            '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                                `<a class="text-white">${category.short}</a>`
                        );
                        $("#nav-course").html("");
                    } else if (category.long) {
                        $("#nav-header").html(category.long);
                        $("#nav-department").html(
                            '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                                `<a onclick="return filterByCategory('all', 'All Non-Textbooks')" href="/shop?nonbook=all">Non-Textbooks</a>`
                        );
                        $("#nav-course").html(
                            '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                                `<a class="text-white">${category.short}</a>`
                        );
                    }
                }
                // else {
                //     // $("#nav-header").html("All Categories");
                //     $("#nav-department").html("");
                //     $("#nav-course").html("");
                // }
                $("#reloading-content").html(response.html);
            },
            beforeSend: function () {
                $("#posts-spinner").addClass("loading");

                $("#items-list").hide();
            },
            complete: function () {
                $("#posts-spinner").removeClass("loading");
                getDataRequest = false;
            },
            error: function (xhr) {
                displayErrorMessage("Error occurred due to invalid Behavior!");
                return;
            },
        });
    }
    // //start at top of page on first load but then scroll to top bar everytime after
    // if (first === true) {
    //     $(window).scrollTop(0);
    // } else {
    //     $(document.body).scrollTop($("#shop-top-bar").offset().top);
    // }
};

function clearAllActiveSelections() {
    let sortActive = document.getElementsByClassName(
        "sort dropdown-item active"
    );
    let sortDisabled = document.getElementsByClassName(
        "sort dropdown-item disabled"
    );
    let filterActive = document.getElementsByClassName(
        "filter dropdown-item active"
    );
    let showActive = document.getElementsByClassName(
        "show dropdown-item active"
    );

    if (sortActive.length > 0) {
        sortActive[0].classList.remove("active");
        sortSwitch("default");
    }
    if (sortDisabled.length > 0) {
        sortDisabled[0].classList.remove("disabled");
        sortSwitch("default");
    }
    if (filterActive.length > 0) {
        filterActive[0].classList.remove("active");
        filterSwitch("default");
    }
    if (showActive.length > 0) {
        showActive[0].classList.remove("active");
        showSwitch("default");
    }
}
function insertBeforeLastOccurrence(strToSearch, strToFind, strToInsert) {
    var n = strToSearch.lastIndexOf(strToFind);
    if (n < 0) return strToSearch;
    return strToSearch.substring(0, n) + strToInsert + strToSearch.substring(n);
}

const show = (ele, term, push) => {
    let reclicked = false;
    let active = document.getElementsByClassName("show dropdown-item active");
    if (active.length > 0 && ele != active[0]) {
        active[0].classList.remove("active");
    }

    if (ele.classList.contains("active")) {
        ele.classList.remove("active");
        reclicked = true;
    } else {
        ele.classList.add("active");
    }

    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;

    if (term === "all" && !reclicked) {
        search_params.set("show", "all");
    } else {
        search_params.delete("show");
        term = "default";
    }
    showSwitch(term);
    search_params.delete("page");
    url.search = search_params.toString();
    let params = url.toString().replace("/data", "");
    params = params.substring(params.lastIndexOf("/") + 1);
    if (push) {
        history.pushState(null, "", params);
        getData(url.toString());
    }
};

const filterByPrice = (ele, filter, push) => {
    let reclicked = false;
    let active = document.getElementsByClassName("filter dropdown-item active");
    if (active.length > 0 && ele != active[0]) {
        active[0].classList.remove("active");
    }

    if (ele.classList.contains("active")) {
        ele.classList.remove("active");
        reclicked = true;
    } else {
        ele.classList.add("active");
    }

    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;
    if (reclicked) {
        search_params.delete("filter");
        filter = "default";
    } else {
        search_params.set("filter", filter);
    }
    filterSwitch(filter);

    search_params.delete("page");
    url.search = search_params.toString();
    let params = url.toString().replace("/data", "");
    params = params.substring(params.lastIndexOf("/") + 1);
    if (push) {
        history.pushState(null, "", params);
        getData(url.toString());
    }
};

const getAll = () => {
    var url = new URL(window.location.href.split("?")[0] + "/data");
    let search_params = url.searchParams;

    browseCollapse();
    clearAllActiveSelections();
    history.pushState(null, "", "shop");
    search_params.delete("department");
    search_params.delete("show");
    search_params.delete("filter");
    search_params.delete("sort");
    search_params.delete("nonbook");
    search_params.delete("search");
    search_params.delete("class");

    url.search = search_params.toString();

    let school = localStorage.getItem("school");
    document.getElementById("nav-header").innerHTML = getSchoolName(school);

    $("#nav-department").html("");
    $("#nav-course").html("");
    getData(url);
};

const getFromPage = (page_num) => {
    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;

    search_params.set("page", page_num);

    url.search = search_params.toString();
    let params = url.toString().replace("/data", "");
    params = params.substring(params.lastIndexOf("/") + 1);
    history.pushState(null, "", params);

    getData(url.toString());
};

const filterByClass = (class_id) => {
    browseCollapse();

    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;

    search_params.set("class", class_id);
    search_params.delete("department");
    search_params.delete("show");
    search_params.delete("filter");
    search_params.delete("sort");
    search_params.delete("nonbook");
    search_params.delete("search");
    clearAllActiveSelections();

    url.search = search_params.toString();

    history.pushState(null, "", `?class=${class_id}`);

    getData(url.toString());

    return false;
};

const filterByDepartment = (department_id) => {
    browseCollapse();
    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;

    search_params.set("department", department_id);
    search_params.delete("class");
    search_params.delete("search");
    search_params.delete("show");
    search_params.delete("filter");
    search_params.delete("sort");
    search_params.delete("nonbook");
    clearAllActiveSelections();

    url.search = search_params.toString();

    history.pushState(null, "", `?department=${department_id}`);

    getData(url.toString());

    return false;
};

const filterByCategory = (term, name) => {
    browseCollapse();
    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;

    search_params.set("nonbook", term);
    search_params.delete("class");
    search_params.delete("show");
    search_params.delete("filter");
    search_params.delete("sort");
    search_params.delete("department");
    search_params.delete("search");

    clearAllActiveSelections();

    url.search = search_params.toString();

    history.pushState(null, "", `?nonbook=${term}`);

    if (name === "All Non-Textbooks") {
        $("#nav-header").html(name);
        $("#nav-department").html(
            '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                `<a class="text-white">Non-Textbooks</a>`
        );
        $("#nav-course").html("");
    } else if (name) {
        $("#nav-header").html(name);
        $("#nav-department").html(
            '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                `<a onclick="return filterByCategory('all', 'All Non-Textbooks')" href="/shop?nonbook=all">Non-Textbooks</a>`
        );
        $("#nav-course").html(
            '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                `<a class="text-white">${name}</a>`
        );
    }
    getData(url.toString());

    return false;
};

var disabled;
const sort = (ele, order, push) => {
    let reclicked = false;
    let active = document.getElementsByClassName("sort dropdown-item active");
    if (active.length > 0 && ele != active[0]) {
        active[0].classList.remove("active");
    }
    if (order === "newest") {
        ele.classList.add("disabled");
        disabled = ele;
    } else {
        if (ele.classList.contains("active")) {
            ele.classList.remove("active");
            reclicked = true;
        } else {
            ele.classList.add("active");
        }
        if (disabled) disabled.classList.remove("disabled");
    }

    let url;
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }
    let search_params = url.searchParams;

    if (reclicked) {
        search_params.delete("sort");
        order = "default";
    } else {
        search_params.set("sort", order);
    }
    sortSwitch(order);
    search_params.delete("page");
    url.search = search_params.toString();
    let params = url.toString().replace("/data", "");
    params = params.substring(params.lastIndexOf("/") + 1);

    if (push) {
        history.pushState(null, "", params);
        getData(url.toString());
    }
};

function displayErrorMessage(message) {
    toastr.options = { positionClass: "toast-top-center", closeButton: true };
    toastr.error(message);
}

var loadedDepartment = {};

function initializeShopPage() {
    let url;
    loadedDepartment = {};
    if (window.location.href.includes("?")) {
        url = new URL(
            insertBeforeLastOccurrence(window.location.href, "?", "/data")
        );
    } else {
        url = new URL(window.location.href + "/data");
    }

    let sort_term = url.searchParams.get("sort");
    let filter_term = url.searchParams.get("filter");
    let show_term = url.searchParams.get("show");

    if (sort_term) {
        const sort_element = document.getElementById(sort_term);
        if (sort_element) {
            sort(document.getElementById(sort_term), sort_term, false);
        } else {
            displayErrorMessage("Invalid sort option!");
        }
    }

    if (filter_term) {
        const filter_element = document.getElementById(filter_term);
        if (filter_element) {
            filterByPrice(
                document.getElementById(filter_term),
                filter_term,
                false
            );
        } else {
            displayErrorMessage("Invalid filter option!");
        }
    }

    if (show_term) {
        const show_element = document.getElementById(show_term);
        if (show_element) {
            show(document.getElementById(show_term), show_term, false);
        } else {
            displayErrorMessage("Invalid show option!");
        }
    }
    browseCollapse();
    getData(url.toString());
}

const browseCollapse = () => {
    if (document.documentElement.clientWidth < 768) {
        if (
            $("#browse-categories")[0].classList.contains("collapsed") !== true
        ) {
            $(".browse-collapse").collapse("toggle");
        }
    }
};

let deletedItems = new Object();

const onSavedDelete = (index, name, id, url) => {
    deletedItems[index] = document.getElementById(`row-${index}`).innerHTML;

    const deletedRow = $(`#row-${index}`);
    const itemUrl = `/shop/${id}`;
    deletedRow.html(
        `<td colspan='4' class='deleted-item'>Deleted <a href="javascript:;" onclick="onItemClick('${itemUrl}')">${name}</a> from your bag
        <a href="javascript:;" onclick="onSavedUndo(${index}, ${id})">Undo</a></td>`
    );
    $.ajax({
        url: url,
        type: "post",
        beforeSend: function (xhr, settings) {
            if (
                !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
                !this.crossDomain
            ) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        },
        success: function () {
            let bagIcon = document.getElementsByClassName("fa-stack")[0];
            bagIcon.setAttribute(
                "data-count",
                parseInt(bagIcon.getAttribute("data-count")) - 1
            );
        },
    });

    saved_html = null;
};

const messageClicked = (id) => {
    let url = `/messagebuyerform`;
    history.replaceState(null, "", `?item=${id}`);
    $.ajax({
        url: url,
        type: "GET",
        async: true,
        success: function (response) {
            $(`#message-modal`).html(
                '<div class="content-section"> \
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"> \
        <span aria-hidden="true">&times;</span> \
         </button>' +
                    response +
                    "</div>"
            );
        },
        beforeSend: function () {
            $(`#message-modal`).html("");
            $(`.modal-content`).toggleClass("loading");
        },
        complete: function () {
            $(`.modal-content`).toggleClass("loading");
        },
    });
};

const onSavedUndo = (index, id) => {
    $.ajax({
        type: "POST",
        url: "/add-to-bag",
        data: { item_id: id },
        success: function (data) {
            if (data.added) {
                let bagIcon = document.getElementsByClassName("fa-stack")[0];
                bagIcon.setAttribute(
                    "data-count",
                    parseInt(bagIcon.getAttribute("data-count")) + 1
                );
            }
        },
        beforeSend: function (xhr, settings) {
            if (
                !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
                !this.crossDomain
            ) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        },
    });

    document.getElementById(`row-${index}`).innerHTML = deletedItems[index];
    const confirmAcc = document.getElementsByClassName("confirm-acc")[
        index - 1
    ];
    if (confirmAcc)
        confirmAcc.addEventListener(
            "click",
            linkClicked.bind(null, null, "/account")
        );
    const savedMessage = document.getElementsByClassName("saved-message")[
        index - 1
    ];
    if (savedMessage)
        savedMessage.addEventListener(
            "click",
            messageClicked.bind(null, savedMessage.id)
        );
};

const initializeSingleProductPage = () => {
    var numImages = document.getElementsByClassName("single-prd-item").length;

    if (numImages <= 1) {
        $(".s_Product_carousel").owlCarousel({
            items: 1,
            autoplay: false,
            autoplayTimeout: 5000,
            loop: false,
            nav: false,
            dots: false,
        });
    } else {
        $(".s_Product_carousel").owlCarousel({
            items: 1,
            loop: true,
        });
    }
};

onItemDelete = (url, name, num, origin) => {
    $.ajax({
        url: url,
        type: "post",
        data: { standalone: origin },
        async: true,
        success: function (response) {
            // location.reload();
            // $("#block-content").html(response.html);
            if (origin === "shop") {
                initializeShopPage();
            } else if (origin === "listings") {
                $("#block-content").html(response.html);
            } else if (origin === "single") {
                linkClicked(document.getElementById("shop"), "/shop");
            }
            toastr.options = {
                positionClass: "toast-top-center",
                closeButton: true,
            };
            toastr.success(`Post ${name} Deleted!`);
        },
        beforeSend: function (xhr, settings) {
            if (
                !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
                !this.crossDomain
            ) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
            $("body").toggleClass("loading");
            $(`#deleteModal${num}`).modal("hide");
            $("#loader-text").html(`Deleting "${name}"...`);
        },
        complete: function () {
            $("body").toggleClass("loading");
            $("#loader-text").html("Loading...");
        },
    });
    listings_html = null;
};

//shop
var itemRequest = null;
function onItemClick(url) {
    history.pushState(null, null, url);
    itemRequest = $.ajax({
        url: url,
        type: "get",
        data: { standalone: "true" },
        async: true,
        success: function (response) {
            $("#block-content").html(response);
        },
        beforeSend: function () {
            $("body").toggleClass("loading");
        },
        complete: function () {
            $("body").toggleClass("loading");
            // if (path === 'shop') {
            //   initializeShopPage();
            // }
        },
    });
    $(window).scrollTop(0);
}

//layout
const highlightNavLink = () => {
    let path = (window.location.pathname + location.search).split("/")[1];
    let active;
    let ending = " | Unibooks";

    if (path === "saved?cart" || path === "saved") {
        active = document.getElementById("shopping-cart");
        document.title = "Shopping Cart" + ending;
    } else if (path === "listings") {
        active = document.getElementById("user");
        document.title = "Listings" + ending;
    } else if (path === "account") {
        active = document.getElementById("user");
        document.title = "Account" + ending;
    } else if (path === "item") {
        active = document.getElementById("sell");
        document.title = "Create Posting" + ending;
    } else if (path === "aboutus") {
        active = document.getElementById("home");
        document.title = "About Us" + ending;
    } else if (path === "contactus") {
        active = document.getElementById("home");
        document.title = "Contact Us" + ending;
    } else if (path.includes("help?d=")) {
        active = document.getElementById("home");
        document.title = "Help" + ending;
    } else if (path === "home" || path === "") {
        active = document.getElementById("home");
        document.title = "Unibooks | The Ultimate University Marketplace";
    } else if (path === "legal") {
        active = document.getElementById("home");
        document.title = "Terms of Service" + ending;
    } else if (path === "privacy") {
        document.title = "Private Policy" + ending;
    } else {
        document.title = path.charAt(0).toUpperCase() + path.slice(1) + ending;
        active = document.getElementById(path.split("?")[0]);
    }
    if (active) {
        let prevActive = document.getElementsByClassName("activable active")[0];
        if (prevActive) {
            prevActive.classList.remove("active");
        }

        active.classList.add("active");
    }
};

//listings
let prevModal = null;
const listingEditClicked = (id, item_category, item_class, item_department) => {
    let url = `/editform/${id}`;
    if (prevModal) {
        prevModal.empty();
    }
    $.ajax({
        url: url,
        type: "GET",
        async: true,
        success: function (response) {
            $(`#modal-body-${id}`).html(response);
            if (item_category !== "None") {
                let category_select = document.getElementById("category_list");
                category_select.value = item_category;

                var $category_select = $(category_select);
                var category_selectize = $category_select[0].selectize;
                category_selectize.setValue(item_category);
            } else {
                let class_select = document.getElementById("class_list");
                let department_select = document.getElementById(
                    "department_list"
                );
                class_select.value = item_class;
                department_select.value = item_department;

                var $department_select = $(
                    document.getElementById("department_list")
                );
                var department_selectize = $department_select[0].selectize;
                department_selectize.setValue(item_department);

                var $class_select = $(document.getElementById("class_list"));
                var class_selectize = $class_select[0].selectize;
                class_selectize.setValue(item_class);
            }
        },
        beforeSend: function () {
            $(`#modal-body-${id}`).html("");
            $(`.modal-content-${id}`).toggleClass("loading");
        },
        complete: function () {
            $(`.modal-content-${id}`).toggleClass("loading");
            prevModal = $(`#modal-body-${id}`);
        },
    });
};

const getSchoolName = (id) => {
    switch (id) {
        case "1":
            return "Pacific University";
        case "2":
            return "Portland State University";
        case "3":
            return "Portland Community College";
    }

    return "School Not Set";
};

const setSchoolName = (id) => {
    const name = getSchoolName(id);
    const normal = document.getElementById("school-name-normal");
    const mobile = document.getElementById("school-name-mobile");
    const footer = document.getElementById("school-name-footer");
    normal.innerHTML = name;
    mobile.innerHTML = name;
    footer.innerHTML = name + " - ";
};

const loadCourses = (department) => {
    if (!(department in loadedDepartment)) {
        $(`#nav${department}`)
            .append(`<div class="d-flex justify-content-center">
    <div class="spinner-border text-secondary" role="status"><span class="sr-only">Loading...</span></div></div>`);
        fetch("/class/" + department)
            .then(function (response) {
                response.json().then(function (data) {
                    for (let item_class of data.classes) {
                        $(`#nav${department}`)
                            .append(`<li class="main-nav-list child"><a href="javascript:filterByClass(${
                            item_class.id
                        })">${item_class.class_name}<span class="number" \
                id="class_total${item_class.id}">${
                            item_class.count ? item_class.count : ""
                        }</span></a></li>`);
                    }
                });
            })
            .then((res) => {
                $(`.spinner-border.text-secondary`).remove();
            });
        loadedDepartment[department] = true;
    }
};