function image_attach(GA){
        user=GA.currentUser.get();
        url = user.getBasicProfile().getImageUrl();
        $('#thumbnail').attr('src', url);
}

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
}

function main_set(url, active){
        let navs = $('.nav-link');
        for (let i in navs) {
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
        main_post(url)
}

function main_post(url){
    let main_block  = $('#main_block');
    main_block[0].dataset.source = url;
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            if (this.responseText != '') {
                let response = (this.responseText);
                $('#main_block')[0].innerHTML = response;
                }
                else {
                }
            }
        };
    xhttp.open("POST", url, true);
    xhttp.setRequestHeader('Content-Type',"application/x-www-form-urlencoded");
    xhttp.send("");
}

function main_refresh(){
    let main_block  = $('#main_block');
    let url = main_block[0].dataset.source;
    main_post(url)
}

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
    });
