
$(document).ready(function(){

    if ($("#header").length){
        var header = $("#header");
        header.css({"background": "url(./images/bg.jpg)"});
//        var cur_bg_position = parseInt(header.css("background-position").split(" ")[1]);
	var cur_bg_position = 0;
        
        setInterval(function(){
            header.css({"background-position": "50% " + "-" + cur_bg_position +"px"});
            cur_bg_position = cur_bg_position +0.5;
            }, 2)
        }

    var promo_bord = $("div.promo");
    if (promo_bord.length){
        var slides = $("div.bord>div");
        var slides_count = slides.length+1;
        var slide_current = 0;
        var tor = $("#toR");
        var tol = $("#toL");
        tor.click(function(){
            var next_slide = slide_current + 1 == slides_count ? 0 : slide_current + 1;
            promo_bord.scrollTo($(slides)[next_slide], 2000, {axis:"x"});
            slide_current = next_slide;
            clearInterval(t);
            t = setInterval(function(){tor.click()}, 7000);
            return false;
            }) // click
        tol.click(function(){
            var next_slide = slide_current != 0 ? slide_current - 1 : slides_count -1;
            promo_bord.scrollTo($(slides)[next_slide], 2000, {axis:"x"});
            slide_current = next_slide;
            clearInterval(t);
            t = setInterval(function(){tol.click()}, 7000);
            return false;
            }) // click
        var t = setInterval(function(){tor.click()}, 7000);
        }

    promo_links = $("div#promo li h1 a");
    promo_blocks = $("div#promo li div");
    promo_parents = $("div#promo li");

    promo_links.each(function(e){
        $(this).click(function(){
            promo_blocks.hide();
            promo_parents.removeClass('active');
//             promo_blocks.fadeOut();
//             $(promo_blocks[e]).show();
            $(promo_parents[e]).addClass('active');
            $(promo_blocks[e]).fadeIn();
            return false;
            })
        })

    function validate_email_phone(message){
        /* E-Mail validator from http://xyfer.blogspot.com/2005/01/javascript-regexp-email-validator.html */
        var em = /(("[\w-\s]+")|([\w-]+(?:\.[\w-]+)*)|("[\w-\s]+")([\w-]+(?:\.[\w-]+)*))(@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][0-9]\.|1[0-9]{2}\.|[0-9]{1,2}\.))((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9]{1,2})\.){2}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9]{1,2})\]?)/ig;
        var ph = /(\+\d)*\s*(\(\d{3}\)\s*)*\d{3}(-{0,1}|\s{0,1})\d{2}(-{0,1}|\s{0,1})\d{2}/g;
        var e_ok = false;
        var p_ok = false;
        if (message.match(em)) e_ok = true;
        if (message.match(ph)) p_ok = true;
        return e_ok || p_ok;
        }

    function validate_email(message){
        var em = /(("[\w-\s]+")|([\w-]+(?:\.[\w-]+)*)|("[\w-\s]+")([\w-]+(?:\.[\w-]+)*))(@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][0-9]\.|1[0-9]{2}\.|[0-9]{1,2}\.))((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9]{1,2})\.){2}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9]{1,2})\]?)/ig;
        var e_ok = false;
        if (message.match(em)) e_ok = true;
        return e_ok;
        }

    function validate_phone(message){
        var ph = /(\+\d)*\s*(\(\d{3}\)\s*)*\d{3}(-{0,1}|\s{0,1})\d{2}(-{0,1}|\s{0,1})\d{2}/g;
        var p_ok = false;
        if (message.match(ph)) p_ok = true;
        return p_ok;
        }

    function validate_length(message){
            return message.length > 15 ? true : false;
        }

    contact_form = $("form.contact");
    if (contact_form.length){
            var trying = 0;
            can_send = false;
            $("#soobshenie").get(0).onkeyup = function(){
                trying = 0;
                $("p#nocontact").fadeOut("slow");
                $("p#bred").fadeOut("slow");
            }

            contact_form.get(0).onsubmit = function(){
                trying +=1;
                message = $("#soobshenie").val();

                ml_ok = validate_length(message);
                if (!ml_ok) {
                        $("p#bred").show();
                    }

                co_ok = validate_email_phone(message);
                if (!co_ok){
                        $("p#nocontact").show();
                    }

                if (!(ml_ok && co_ok)){
                    if (trying < 2){
                        return false;
                        }
                    }

                $.post("http://yed-prior.com/mailme.php", {soobshenie: $("#soobshenie").val()},
                    function(){
                        $("#soobshenie").val("");
                        $("p.confirm").fadeIn("slow");
                        return false;
                        });
                return false;
                }
        }

    order_form = $("form.order");
    if (order_form.length){

            $("#who").get(0).onblur = function(){
                if (!$(this).val()) {
                    $(this).parent().addClass('required');
                    }
                }
            $("#who").get(0).onfocus = function(){
                $(this).parent().removeClass('required');
                }
            $("#email").get(0).onblur = function(){
                if (!validate_email($(this).val())) {
                    $(this).parent().addClass('required');
                    }
                }
            $("#email").get(0).onfocus = function(){
                $(this).parent().removeClass('required');
                }
            $("#phone").get(0).onblur = function(){
                if (!validate_phone($(this).val())) {
                    $(this).parent().addClass('required');
                    }
                }
            $("#phone").get(0).onfocus = function(){
                $(this).parent().removeClass('required');
                }

            order_form.get(0).onsubmit = function(){
                send = true;
                if (!$("#who").val()) {$("#who").parent().addClass('required'); send=false};
                if (!validate_email($("#email").val())) {$("#email").parent().addClass('required'); send=false};
                if (!validate_phone($("#phone").val())) {$("#phone").parent().addClass('required'); send=false};

                if (send){
                    $.post("http://yed-prior.com/orderme.php", {message: $("#message").val(),
                        who: $("#who").val(),
                        email: $("#email").val(),
                        phone: $("#phone").val(),
                        organization: $("#organization").val(),
                        kind: $("#kind").val(),
                        month: $("#month").val(),
                        price: $("#price").val()
                    },
                    function(){
                        $("#message").val("");
                        $("#who").val("");
                        $("#email").val("");
                        $("#phone").val("");
                        $("#organization").val("");
                        $("#kind").val("");
                        $("#month").val("");
                        $("#price").val("");
                        $("#confirm").fadeIn("slow");
                        return false;
                        });
                    };
                return false;
                }
        }

$("#toSpec").toggle(function(){$(".special").animate({"marginTop":0},1000);return false;}, function(){$(".special").animate({"marginTop":-93},1000); return false;})


$(".makeOrder a").click(function(){
    $(".iBg").fadeIn("slow");
    $(".iOrder").fadeIn("slow");
    return false;
    }) // click
    $(".iOrder a.close").click(function(){
        $(".iOrder").fadeOut("slow");
        $(".iBg").fadeOut("slow");
        return false;
        }) // click

})
