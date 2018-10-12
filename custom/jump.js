function image_attach(GA){
        user=GA.currentUser.get();
        url = user.getBasicProfile().getImageUrl();
        $('#thumbnail').attr('src', url);
};

function google_init() {
    gapi.load('auth2', function() {
            GA = gapi.auth2.init({
                    'client_id': '374851329008-r1a7p9779hcqsf7go31pr7cnthvea0tf.apps.googleusercontent.com',
                    'fetch_basic_profile': true,
            });
            GA.then(function () {
                if (GA.isSignedIn.get()) {
                    image_attach(GA)
                }
                else {
                    GA.signIn().then( function() {
                        image_attach(GA)
                })}
            })
        });
};

function main_set(url,active, auto){
        menu_set(active);
        main_post(url);
        main_block = $('#main_block')[0];
        main_block.dataset.source = url;
        main_block.dataset.auto = auto;
};

function side_set(url_main, url_sb, active, auto) {
        menu_set(active);
        side_post(url_sb);
        main_post(url_main);
        main_block = $('#main_block')[0];
        main_block.dataset.source = url_main;
        main_block.dataset.auto = auto;
};

function menu_set(active){
        let navs = $('.nav-link');
        for (i = 0; i < navs.length; i++) {
            let nav = navs[i];
            try {
            nav.classList.remove('active');
            }
            catch (err){

            }
        }
        let nav = $('#' + active)[0];
        try {
            nav.classList.add('active');
        }
        catch (err){
                alert(err)
        }
        $('.collapse').collapse('hide');

};

function main_post(url) {
    let main_block  = $('#main_block')[0];
    post(main_block,url);
};

function side_post(url) {
    let side_bar = $('#side_bar')[0];
    post(side_bar,url);
};

function post(element, url){
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            if (this.responseText != '') {
                let response = (this.responseText);
                element.innerHTML = response;
                after_refresh();
            }
            }
        };
    xhttp.open("POST", url, true);
    xhttp.setRequestHeader('Content-Type',"application/x-www-form-urlencoded");
    xhttp.send("");
};

function main_refresh(){
    let main_block  = $('#main_block')[0];
    let url = main_block.dataset.source;
    auto_flag = main_block.dataset.auto;
    if ( auto_flag == 'true' ) {
        main_post(url);
    }
};

function after_refresh() {
$('.form_datetime').datetimepicker({
        //language:  'en',
        weekStart: 1,
        todayBtn:  1,
		autoclose: 1,
		todayHighlight: 1,
		startView: 2,
		forceParse: 0,
        showMeridian: 1
});
$('.form_date').datetimepicker({
        language:  'en',
        weekStart: 1,
        todayBtn:  1,
		autoclose: 1,
		todayHighlight: 1,
		startView: 2,
		minView: 2,
		forceParse: 0
});
$('.form_time').datetimepicker({
        language:  'en',
        weekStart: 1,
        todayBtn:  0,
		autoclose: 1,
		todayHighlight: 1,
		startView: 1,
		minView: 0,
		maxView: 1,
		forceParse: 0
})};

function new_submit(form_id,url) {
           // from https://stackoverflow.com/questions/18169933/submit-form-without-reloading-page
           $.ajax({
             type: 'post',
             url: url,
             data: $('#' + form_id).serialize(),
             success: function(data)
             {
                 $('#main_block')[0].innerHTML = data;
                 after_refresh()
             }
         });
            return false ;
}

