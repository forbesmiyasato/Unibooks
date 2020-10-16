using System;
using System.Collections.Generic;
using System.IO;
using Innostudio;
using Newtonsoft.Json;

public partial class Upload : System.Web.UI.Page
{
    public void Page_Load(object sender, EventArgs e)
    {

        // method POST
        if (Request.HttpMethod == "POST")
        {
            string type = Request.QueryString["type"];
            string uploadDir = "~/uploads/";

            switch (type)
            {
                case "upload":
                    // initialize fileuploader
                    FileUploader fileUploader = new FileUploader("files", new Dictionary<string, dynamic>() {
                        { "limit", 1 },
                        { "title", "auto" },
                        { "uploadDir", uploadDir }
                    });

                    // upload process
                    var data = fileUploader.Upload();

                    // response
                    if (data["files"].Count == 1)
                        data["files"][0].Remove("file");
                    Response.Write(JsonConvert.SerializeObject(data));
                    break;
                case "remove":
                    string file = Request.Form["file"];

                    if (file != null)
                    {
                        file = FileUploader.FullDirectory(uploadDir) + file;

                        if (File.Exists(file))
                            File.Delete(file);
                    }
                    break;
            }

            Response.End();
        }
    }
}