export const defaultInterviewTemplate = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 30px 25px; }
        .btn { display: inline-block; background-color: #007bff; color: #ffffff !important; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
        .footer { background-color: #f9f9f9; padding: 15px; border-top: 1px solid #e0e0e0; text-align: center; font-size: 11px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Resume Shortlisted</h1>
        </div>
        <div class="content">
            <p>Hi <b>{name}</b>,</p>
            <p>We are pleased to inform you that your resume has been shortlisted for the <b>Intern position</b>.</p>
            <p>To move forward, please confirm your availability for the interview by filling out the form below:</p>
            
            <div style="text-align: center;">
                <a href="{form_url}" class="btn">Confirm Availability</a>
            </div>
            
            <p>Please ensure you are available at your chosen time slot. We look forward to interacting with you!</p>

            <p style="margin-bottom: 5px; margin-top: 30px;">Thanks and Regards,</p>
            <p style="margin-top: 0; color: #0056b3; font-weight: bold; font-size: 16px;">Team HR</p>
        </div>
        <div class="footer"><p>© 2026 HR-Automation</p></div>
    </div>
</body>
</html>`

export const defaultOfferTemplate = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 30px 25px; }
        .footer { background-color: #f9f9f9; padding: 15px; border-top: 1px solid #e0e0e0; text-align: center; font-size: 11px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome Aboard!</h1>
        </div>
        <div class="content">
            <p>Dear <b>{name}</b>,</p>
            
            <p style="color: #0056b3; font-weight: bold; font-size: 18px; text-align: center;">Congratulations and Welcome!</p>
            
            <p>We are happy to appoint you as a <b>{role}</b>.</p>
            <p>Please find enclosed the <b>offer letter</b>.</p>
            
            <div style="background-color: #f0f7ff; padding: 15px; border-left: 4px solid #0056b3; margin: 20px 0;">
                <p style="margin: 0;">We would like to have you on board by <b>{start_date}</b>.</p>
            </div>

            <p style="font-size: 13px; color: #666;"><i>This offer is subject to reference checks and if not accepted, will expire by the end of <b>{expiry_date}</b>.</i></p>

            <p style="margin-bottom: 5px; margin-top: 30px;">Thanks and Regards,</p>
            <p style="margin-top: 0; color: #0056b3; font-weight: bold; font-size: 16px;">Team HR</p>
        </div>
        <div class="footer"><p>© 2026 HR-Automation</p></div>
    </div>
</body>
</html>`

export const defaultCertificateTemplate = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 30px 25px; }
        .footer { background-color: #f9f9f9; padding: 15px; border-top: 1px solid #e0e0e0; text-align: center; font-size: 11px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Internship Completed!</h1>
        </div>
        <div class="content">
            <p>Dear <b>{name}</b>,</p>
            
            <p style="color: #0056b3; font-weight: bold; font-size: 18px; text-align: center;">Congratulations on completing your journey!</p>
            
            <p>We are delighted to share your <b>Completion Certificate</b> attached to this email.</p>
            <p>We wish you all the best in your future endeavors!</p>

            <p style="margin-bottom: 5px; margin-top: 30px;">Thanks and Regards,</p>
            <p style="margin-top: 0; color: #0056b3; font-weight: bold; font-size: 16px;">Team HR</p>
        </div>
        <div class="footer"><p>© 2026 HR-Automation</p></div>
    </div>
</body>
</html>`
