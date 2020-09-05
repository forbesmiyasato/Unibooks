function getParameterByName(name) {
    var match = RegExp("[?&]" + name + "=([^&]*)").exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}

const showSwitch = (show_term) => {
    console.log(show_term);
    switch (show_term) {
        case "all":
            $("#show-button-text").html("Showing All");
            break;
        default:
            $("#show-button-text").html("Show All");
            break;
    }
};
const filterSwitch = (filter_term) => {
    console.log(filter_term);
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
            console.log("default!!!");
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
const getData = (url) => {
    console.log(url);
    $.ajax({
        url: url,
        type: "get",
        data: null,
        success: function (response) {
            // console.log(response)
            let course = response.course;
            let department = response.department;
            let search = response.search;
            let numResults = response.numResults;
            // let sort = response.sort
            // let filter = response.filter
            // let show = response.filter
            if (course) {
                $("#nav-header").html(course.name);
                $("#nav-department").html(
                    '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                        `<a href="javascript:filterByDepartment(${department.id})">${department.name}</a>`
                );
                $("#nav-course").html(
                    '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                        `<a class="text-white">${course.name}</a>`
                );
            } else if (department) {
                $("#nav-header").html(department.name);
                $("#nav-department").html(
                    '<span class="lnr lnr-arrow-right banner-arrow"></span>' +
                        `<a class="text-white">${department.name}</a>`
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
            } else {
                $("#nav-header").html("All Categories");
                $("#nav-department").html("");
                $("#nav-course").html("");
            }
            $("#posts-spinner").toggleClass("loading");

            $("#reloading-content").html(response.html);
        },
        beforeSend: function () {
            console.log("item list before send");
            $("#posts-spinner").toggleClass("loading");
            $("#items-list").hide();
        },
        complete: function () {
            // $("#posts-spinner").toggleClass("loading");
        },
        error: function (xhr) {
            getAll(); // return to main shop page on invalid query caused by user messing with url params
        },
    });
};

function clearAllActiveSelections() {
    console.log("Activated");
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

    console.log("111", filterActive);
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
    console.log(active);
    if (active.length > 0 && ele != active[0]) {
        console.log(active[0]);
        active[0].classList.remove("active");
    }

    console.log(ele);
    if (ele.classList.contains("active")) {
        ele.classList.remove("active");
        reclicked = true;
    } else {
        ele.classList.add("active");
    }

    let url;
    console.log(ele);
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
    }
    console.log(url.toString());
    getData(url.toString());
};

const filterByPrice = (ele, filter, push) => {
    let reclicked = false;
    let active = document.getElementsByClassName("filter dropdown-item active");
    console.log(active);
    if (active.length > 0 && ele != active[0]) {
        console.log(active[0]);
        active[0].classList.remove("active");
    }

    console.log(ele);
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
    }

    console.log(url.toString());
    getData(url.toString());
};

const getAll = () => {
    var url = window.location.href.split("?")[0] + "/data";

    browseCollapse();
    clearAllActiveSelections();
    history.pushState(null, "", "shop");

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

    console.log(url.toString());
    getData(url.toString());
};

const filterByClass = (
    class_id,
    class_name,
    department_id,
    department_name
) => {
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
    clearAllActiveSelections();

    url.search = search_params.toString();

    history.pushState(null, "", `?class=${class_id}`);

    console.log(class_id, class_name, department_name, department_id);
    console.log(url.toString());
    getData(url.toString());
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

    console.log(url);

    search_params.set("department", department_id);
    search_params.delete("class");
    search_params.delete("show");
    search_params.delete("filter");
    search_params.delete("sort");
    clearAllActiveSelections();

    console.log(url);

    url.search = search_params.toString();

    history.pushState(null, "", `?department=${department_id}`);

    console.log(url.toString());
    getData(url.toString());
};

var disabled;
const sort = (ele, order, push) => {
    let reclicked = false;
    let active = document.getElementsByClassName("sort dropdown-item active");
    console.log(active);
    if (active.length > 0 && ele != active[0]) {
        console.log(active[0]);
        active[0].classList.remove("active");
    }
    if (order === "newest") {
        ele.classList.add("disabled");
        disabled = ele;
    } else {
        console.log(ele);
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
    }

    console.log(url.toString());
    getData(url.toString());
};

function initializeShopPage() {
    let url;
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

    console.log(sort_term, filter_term, show_term);

    if (sort_term) {
        sort(document.getElementById(sort_term), sort_term, false);
    }

    if (filter_term) {
        filterByPrice(document.getElementById(filter_term), filter_term, false);
    }

    if (show_term) {
        show(document.getElementById(show_term), show_term, false);
    }

    console.log(url.toString());
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
// $('document').ready(function () {
//    initializeShopPage();
// })

const onSavedDelete = (index, name, id, url) => {
    const deletedRow = $(`#row-${index}`);
    console.log(url);
    deletedRow.html(
        `<td colspan='4' class='deleted-item'>Deleted <a href="/shop/${id}">${name}</a> from your bag</td>`
    );
    $.ajax({
        url: url,
        type: "post",
        success: function () {
            let bagIcon = document.getElementsByClassName("bag-icon")[0];
            bagIcon.innerHTML = parseInt(bagIcon.innerHTML) - 1;
        },
    });
};

const initializeSingleProductPage = () => {
    console.log("invoked");
    var numImages = document.getElementsByClassName("single-prd-item").length;

    if (numImages <= 1) {
        console.log(numImages);
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
        });
    }
};

// $('document').ready(function () {
//    initializeSingleProductPage();
// })

onItemDelete = (url, name, num, origin) => {
    console.log(origin);
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
                positionClass: "toast-top-left",
                closeButton: true,
            };
            toastr.success(`Post ${name} Deleted!`);
        },
        beforeSend: function () {
            $("body").toggleClass("loading");
            console.log(`#deleteModal${num}`);
            $(`#deleteModal${num}`).modal("hide");
            $("#loader-text").html(`Deleting "${name}"...`);
        },
        complete: function () {
            $("body").toggleClass("loading");
            $("#loader-text").html("Loading...");
            // if (path === 'shop') {
            //   initializeShopPage();
            // }
        },
    });
    console.log(url);
};

function onItemClick(url) {
    history.pushState(null, null, url);
    $.ajax({
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
}

const highlightNavLink = () => {
    let path = (window.location.pathname + location.search).split("/")[1];
    let active;
    if (path === "saved?cart") {
        active = document.getElementById("shopping-cart");
    } else if (
        path === "listings" ||
        path === "account" ||
        path === "saved"
    ) {
        active = document.getElementById("user");
    } else if (path === "item") {
        active = document.getElementById("sell");
    } else {
        console.log("!!!!!!!!!!!!", path.split("?")[0])
        active = document.getElementById(path.split("?")[0]);
    }
    console.log(path, active)
    if (active) {
        let prevActive = document.getElementsByClassName("activable active")[0];
        console.log("PREV ACTIVE", prevActive);
        if (prevActive) {
            prevActive.classList.remove("active");
            console.log(prevActive.classList.contains("active"))
        }

        console.log("PATH", path)
        
        active.classList.add("active");
        console.log("ACTIVE", active)
    }
};
