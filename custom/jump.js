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
