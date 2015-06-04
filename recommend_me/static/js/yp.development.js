$(document).ready(function(){
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
        // resizing project tiles
        function resize_tiles(){
            currend_width = $("body").width();
            if (currend_width < 1180) {
                // small sizes
                $("#projects li").width(260);
		$("#projects li.separ").width(80);
                $("#projects li b").width(158);
                $("#projects li a img").width(240);
                }
            else {
                // initial sizes
                $("#projects li").width(335);
		$("#projects li.separ").width(80);
                $("#projects li b").width(233);
                $("#projects li a img").width(300);
                }
            }
        $(window).get(0).onresize = function(){
            resize_tiles();
            }
        resize_tiles();
    })
