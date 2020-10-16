using System;
using System.Collections.Generic;
using Innostudio;
using Newtonsoft.Json;

public partial class Default : System.Web.UI.Page
{
    public void Page_Load(object sender, EventArgs e)
    {
        
        // method POST
        if (Request.HttpMethod == "POST")
        {
            // initialize fileuploader
            FileUploader fileUploader = new FileUploader("files", new Dictionary<string, dynamic>() {
                { "title", "auto" },
                { "uploadDir", "~/uploads/" },
                { "files", new List<Dictionary<string, dynamic>>() }
            });
            
            // upload process
            var data = fileUploader.Upload();
            
            // list of removed files
            var removedFiles = fileUploader.GetRemovedFiles();

            // response
            Response.Write("<pre>");
            Response.Write(JsonConvert.SerializeObject(data));
            Response.Write("</pre>");
            Response.End();
        }
    }
}