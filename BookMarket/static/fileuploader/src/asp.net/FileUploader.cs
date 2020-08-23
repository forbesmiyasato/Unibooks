/**
 * FileUploader
 * Copyright (c) 2020 Innostudio.de
 * Website: https://innostudio.de/fileuploader/
 * Version: 2.2 (12-Mar-2020)
 * Namespace: Innostudio
 * Requires: System, Newtonsoft.Json
 * License: https://innostudio.de/fileuploader/documentation/#license
 */

using System;
using System.Collections.Generic;
using System.Configuration;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Web;
using System.Web.Configuration;
using Newtonsoft.Json;

namespace Innostudio
{
    public class FileUploader
    {
        private readonly Dictionary<string, dynamic> default_options = new Dictionary<string, dynamic>()
        {
            { "limit", null },
            { "maxSize", null },
            { "fileMaxSize", null },
            { "extensions", null },
            { "disallowedExtensions", new string[] { "asp", "aspx", "cs" } },
            { "required", false },
            { "uploadDir", "~/uploads/" },
            { "title", "auto" },
            { "replace", false },
            { "editor", null },
            { "listInput", true },
            { "files", null }
        };

        private HttpRequest Request = HttpContext.Current.Request;

        private Random random = new Random((int)DateTime.Now.Ticks);

        private Dictionary<string, dynamic> field = new Dictionary<string, dynamic>();

        private Dictionary<string, dynamic> listInput;

        protected Dictionary<string, dynamic> options;

        /**
         * __construct method
         *
	     * @public
         * @param name {String}
         * @param options {Dictionary}
         */
        public FileUploader(string name, Dictionary<string, object> options = null)
        {
            // merge options
            this.options = this.mergeOptions(options, this.default_options.ToDictionary(entry => entry.Key, entry => entry.Value));

            // create field array
            this.field.Add("name", name);
            this.field.Add("input", null);
            this.field.Add("count", 0);
            this.listInput = this.readListInput();

            // store input files
            for (int i = 0; i < Request.Files.AllKeys.Length; i++)
            {
                if (Request.Files.AllKeys[i] == field["name"])
                {
                    if (Request.Files[i].FileName.Length == 0)
                        continue;
                    if (field["input"] == null)
                        field["input"] = new List<Dictionary<string, dynamic>>();
                    field["input"].Add(new Dictionary<string, dynamic>()
                    {
                        { "name", Request.Files[i].FileName },
                        { "size", (float)Request.Files[i].ContentLength },
                        { "type", Request.Files[i].ContentType },
                        { "tmp", Request.Files[i] }
                    });

                    field["count"]++;
                }
            }
        }

        public Dictionary<string, dynamic> Upload()
        {
            var data = new Dictionary<string, dynamic>()
            {
                { "hasWarnings", false },
                { "isSuccess", true },
                { "warnings", new List<string>() },
                { "files", new List<Dictionary<string, dynamic>>() }
            };

            if (field["input"] != null)
            {
                var valid = this.validate();
                var chunk = Request.Form["_chunkedd"] != null && field["input"].Count == 1 ? JsonConvert.DeserializeObject<Dictionary<string, dynamic>>(Request.Form["_chunkedd"]) : null;
                var listInput = this.readListInput();

                if (valid is bool && valid == true)
                {
                    foreach (dynamic file in field["input"])
                    {
                        if (chunk != null)
                        {
                            if (chunk.ContainsKey("isFirst") || !chunk.ContainsKey("temp_name"))
                                chunk["temp_name"] = random_string(6) + DateTime.Now.ToString("yyyyMMddHHmmssffff");

                            var tmp = options["uploadDir"] + ".unconfirmed_" + FileUploader.FilterFilename(chunk["temp_name"]);

                            if (!chunk.ContainsKey("isFirst") && !File.Exists(tmp))
                                continue;

                            dynamic fs;
                            if (!File.Exists(tmp))
                                fs = File.Create(tmp);
                            else
                                fs = File.Open(tmp, FileMode.Append);

                            file["tmp"].InputStream.Seek(0, SeekOrigin.Begin);
                            file["tmp"].InputStream.CopyTo(fs);
                            fs.Close();

                            if (chunk.ContainsKey("isLast"))
                            {
                                file["tmp"] = tmp;
                                file["name"] = chunk["name"];
                                file["size"] = chunk["size"];
                                file["type"] = chunk["type"];
                            }
                            else
                            {

                                HttpContext.Current.Response.Write(JsonConvert.SerializeObject(new Dictionary<string, dynamic>()
                                {
                                    { "fileuploader", new Dictionary<string, dynamic>() {
                                        { "temp_name", chunk["temp_name"] }
                                    } }
                                }, Formatting.Indented));
                                HttpContext.Current.Response.End();
                                return null;
                            }
                        }

                        var metas = new Dictionary<string, dynamic>();
                        metas["tmp"] = file["tmp"];
                        metas["extension"] = Path.GetExtension(file["name"]).Replace(".", string.Empty).ToLower();
                        metas["type"] = file["type"];
                        metas["format"] = file["type"].Split('/')[0];
                        metas["name"] = metas["old_name"] = file["name"];
                        metas["title"] = metas["old_title"] = Path.GetFileNameWithoutExtension(file["name"]);
                        metas["size"] = file["size"];
                        metas["size2"] = formatSize(file["size"]);
                        metas["date"] = DateTime.Now.ToString();
                        metas["chunked"] = chunk;

                        // validate file
                        var validFile = validate(metas);
                        var listInputName = "0:/" + metas["old_name"];
                        var fileInList = listInput == null || listInput["list"].IndexOf(listInputName) > -1;

                        if (validFile is bool && validFile == true)
                        {
                            if (fileInList)
                            {
                                if (listInput != null)
                                {
                                    int fileListIndex = listInput["list"].IndexOf(listInputName);
                                    metas["listProps"] = listInput["values"][fileListIndex];
                                    listInput["list"].RemoveAt(fileListIndex);
                                    listInput["values"].RemoveAt(fileListIndex);
                                }
                                
                                metas["i"] = data["files"].Count;
                                metas["name"] = generateFileName(options["title"], metas);
                                metas["title"] = Path.GetFileNameWithoutExtension(metas["name"]);
                                metas["file"] = options["uploadDir"] + metas["name"];
                                metas["replaced"] = File.Exists(metas["file"]);

                                data["files"].Add(metas);
                            }
                        }
                        else
                        {
                            if (metas["chunked"] != null && metas["tmp"] is string && File.Exists(metas["tmp"]))
                                File.Delete(metas["tmp"]);

                            data["isSuccess"] = false;
                            data["hasWarnings"] = true;
                            data["warnings"].Add(validFile);
                            data["files"].Clear();

                            if (fileInList)
                                continue;
                            break;
                        }
                    }

                    if (!data["hasWarnings"])
                    {
                        foreach (dynamic item in data["files"])
                        {
                            var key = data["files"].IndexOf(item);

                            if (item["chunked"] != null ? rename_file(item["tmp"], item["file"]) : upload_file(item["tmp"], item["file"]))
                            {
                                item.Remove("i");
                                item.Remove("chunked");
                                item.Remove("tmp");
                                item["uploaded"] = true;

                                this.options["files"].Add(data["files"][key]);
                            }
                            else
                            {
                                data["files"].RemoveAt(key);
                            }
                        }
                    }

                }
                else
                {
                    data["isSuccess"] = false;
                    data["hasWarnings"] = true;
                    data["warnings"].Add(valid);
                }
            }
            else if (options["required"] && Request.HttpMethod == "POST")
            {
                data["isSuccess"] = false;
                data["hasWarnings"] = true;
                data["warning"].Add(codeToMessage("required_and_no_file"));
            }

            if (listInput != null)
            {
                foreach (dynamic item in GetFileList())
                {
                    var key = GetFileList().IndexOf(item);

                    if (!item.ContainsKey("listProps"))
                    {
                        int fileListIndex = listInput["list"].IndexOf(item["file"]);

                        if (fileListIndex > -1)
                            item["listProps"] = listInput["values"][fileListIndex];
                    }

                    if (item.ContainsKey("listProps"))
                    {
                        item["listProps"].Remove("file");

                        if (item["listProps"].Count == 0)
                            item.Remove("listProps");
                    }
                }
            }

            this.editFiles();
            this.sortFiles();

            return data;
        }

        public dynamic GetOptions()
        {
            return this.options;
        }

        public List<Dictionary<string, dynamic>> GetFileList(string customKey = null)
        {
            var list = new List<Dictionary<string, dynamic>>();

            if (customKey != null)
            {
                foreach (dynamic item in options["files"])
                {
                    dynamic attribute = getFileAttribute(item, customKey);
                    list.Add(attribute ?? item["file"]);
                }
            }
            else
            {
                return options["files"];
            }

            return list;
        }

        public List<Dictionary<string, dynamic>> GetUploadedFiles()
        {
            var list = new List<Dictionary<string, dynamic>>();

            foreach (dynamic item in GetFileList())
            {
                if (item.ContainsKey("uploaded") && item["uploaded"] == true)
                    list.Add(item);
            }

            return list;
        }

        public List<Dictionary<string, dynamic>> GetPreloadedFiles()
        {
            var list = new List<Dictionary<string, dynamic>>();

            foreach (dynamic item in GetFileList())
            {
                if (!item.ContainsKey("uploaded"))
                    list.Add(item);
            }

            return list;
        }

        public List<Dictionary<string, dynamic>> GetRemovedFiles(string customKey = "file")
        {
            var list = new List<Dictionary<string, dynamic>>();

            if (listInput != null && options["files"].Count > 0)
            {
                foreach (dynamic item in options["files"])
                {
                    if (listInput["list"].IndexOf(getFileAttribute(item, customKey)) == -1 && (!item.ContainsKey("uploaded") || !item["uploaded"]))
                    {
                        list.Add(item);
                    }
                }
            }

            foreach(dynamic item in list)
                options["files"].RemoveAt(options["files"].IndexOf(item));

            return list;
        }

        public dynamic GetListInput()
        {
            return listInput;
        }

        private bool upload_file(HttpPostedFile file, string destination)
        {
            if (File.Exists(destination))
                File.Delete(destination);

            file.SaveAs(destination);

            return File.Exists(destination);
        }

        private bool rename_file(string source, string destination)
        {
            File.Move(source, destination);

            return File.Exists(destination);
        }

        private Dictionary<string, dynamic> mergeOptions(Dictionary<string, dynamic> newOptions, Dictionary<string, dynamic> options)
        {
            foreach (var x in newOptions)
            {
                options[x.Key] = x.Value;
            }

            if (options["uploadDir"] != null)
                options["uploadDir"] = FileUploader.FullDirectory(options["uploadDir"]);
            if (options["files"] == null)
                options["files"] = new List<Dictionary<string, dynamic>>();

            return options;
        }

        private dynamic getFileAttribute(dynamic item, string attribute)
        {
            dynamic result = null;

            if (attribute == null)
                return result;
            if (item.ContainsKey("data") && item["data"].ContainsKey(attribute))
                result = item["data"][attribute];
            if (item.ContainsKey(attribute))
                result = item[attribute];

            return result;
        }

        private dynamic validate(Dictionary<string, dynamic> item = null)
        {
            if (item == null)
            {
                if (options["required"] == true && field["count"] + options["files"].Count == 0)
                    return codeToMessage("required_and_no_file");
                if (options["limit"] != null && field["count"] + options["files"].Count > options["limit"])
                    return codeToMessage("max_number_of_files");
                if (!Directory.Exists(options["uploadDir"]))
                    return codeToMessage("invalid_folder_path");

                float totalSize = 0;
                foreach (var file in field["input"]) { totalSize += file["size"]; }
                if (ConfigurationManager.GetSection("system.web/httpRuntime") is HttpRuntimeSection section && totalSize / 1000 > section.MaxRequestLength)
                    return codeToMessage("maxRequestLength");
                if (options["maxSize"] != null && totalSize / 1000000 > (float)options["maxSize"])
                    return codeToMessage("max_files_size");
            }
            else
            {
                if (options["disallowedExtensions"] != null && (Array.IndexOf(options["disallowedExtensions"], item["extension"]) > -1 || Array.IndexOf(options["disallowedExtensions"], item["extension"]) > -1 || Array.IndexOf(options["disallowedExtensions"], item["format"] + "/*") > -1))
                    return codeToMessage("accepted_file_types", item);
                if (options["extensions"] != null && Array.IndexOf(options["extensions"], item["extension"]) == -1 && Array.IndexOf(options["extensions"], item["type"]) == -1 && Array.IndexOf(options["extensions"], item["format"] + "/*") == -1)
                    return codeToMessage("accepted_file_types", item);
                if (options["fileMaxSize"] != null && (float)item["size"] / 1000000 > (float)options["fileMaxSize"])
                    return codeToMessage("max_file_size", item);
            }
            return true;
        }

        private void editFiles()
        {
            if (options["editor"] is bool && options["editor"] == false)
                return;

            foreach (dynamic item in options["files"])
            {
                string file = item.ContainsKey("relative_file") ? item["relative_file"] : item["file"];

                if (item.ContainsKey("listProps") && item["listProps"].ContainsKey("editor"))
                    item["editor"] = item["listProps"]["editor"];
                if (item.ContainsKey("uploaded") && Request.Form["_editorr"] != null && field["count"] == 1)
                    item["editor"] = JsonConvert.DeserializeObject<List<Dictionary<string, dynamic>>>(Request.Form["_editorr"]);

                if (File.Exists(file) && item["type"].IndexOf("image/") == 0)
                {
                    dynamic width = null;
                    dynamic height = null;
                    dynamic quality = 90;
                    dynamic rotation = 0;
                    dynamic crop = false;

                    if (options["editor"] is Dictionary<string, dynamic>)
                    {
                        if (options["editor"].ContainsKey("maxWidth"))
                            width = options["editor"]["maxWidth"];
                        if (options["editor"].ContainsKey("maxHeight"))
                            height = options["editor"]["maxHeight"];
                        if (options["editor"].ContainsKey("quality"))
                            quality = options["editor"]["quality"];
                        if (options["editor"].ContainsKey("crop"))
                            crop = options["editor"]["crop"];
                    }

                    if (item.ContainsKey("editor") && !(item["editor"] is bool))
                    {
                        if (item["editor"].ContainsKey("rotation"))
                            rotation = item["editor"]["rotation"];
                        if (item["editor"].ContainsKey("crop"))
                            crop = item["editor"]["crop"];
                    }

                    FileUploader.Resize(file, width, height, null, crop, quality, rotation);
                }
            }
        }

        private void sortFiles()
        {
            int freeIndex = options["files"].Count;

            foreach (dynamic item in options["files"])
            {
                var key = options["files"].IndexOf(item);

                if (item.ContainsKey("listProps") && item["listProps"].ContainsKey("index"))
                    item["index"] = (int)item["listProps"]["index"];

                if (!item.ContainsKey("index"))
                {
                    item["index"] = freeIndex;
                    freeIndex++;
                }
            }

            if (freeIndex > 0 && options["files"][0].ContainsKey("index"))
            {
                List<Dictionary<string, dynamic>> d = options["files"];
                List<Dictionary<string, dynamic>> files = new List<Dictionary<string, dynamic>>();
                var val = from ele in d orderby ele["index"] ascending select ele;

                foreach (dynamic item in val)
                    files.Add(item);

                options["files"] = files;
            }
        }

        private string generateFileName(dynamic conf, dynamic item, bool skip_replace_check = false)
        {
            conf = conf is string ? new object[] { conf } : conf.Clone();
            string type = conf[0];
            int length = conf is Array && conf.Length > 1 ? Math.Max(1, (int)conf[1]) : 12;
            bool forceExtension = conf is Array && conf.Length > 2 && conf[2] == true;
            string random_string = this.random_string(length);
            string extension = item["extension"].Length > 0 ? "." + item["extension"] : "";
            string name;

            switch (type)
            {
                case null:
                case "auto":
                    name = random_string;
                    break;
                case "name":
                    name = item["title"];
                    break;
                default:
                    name = type;
                    string name_extension = Path.GetExtension(name).Replace(".", string.Empty).ToLower();

                    name = name.Replace("{i}", (item["i"] + 1) + "");
                    name = name.Replace("{random}", random_string);
                    name = name.Replace("{file_name}", item["title"]);
                    name = name.Replace("{file_size}", item["size"] + "");
                    name = name.Replace("{timestamp}", DateTime.Now.ToString("yyyyMMddHHmmssffff"));
                    name = name.Replace("{date}", DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss"));
                    name = name.Replace("{extension}", item["extension"]);
                    name = name.Replace("{format}", item["format"]);
                    name = name.Replace("{index}", (item.ContainsKey("listProps") && item["listProps"].ContainsKey("index") ? item["listProps"]["index"] : 0) + "");

                    if (forceExtension && name_extension.Length > 0)
                    {
                        if (name_extension != "{extension}")
                        {
                            type = type.Substring(0, -1 * (name_extension.Length + 1));
                            extension = item["extension"] = name_extension;
                        }
                        else
                        {
                            type = type.Substring(0, -1 * (item["extension"].Length + 1));
                            extension = "";
                        }
                    }
                    break;
            }

            if (extension.Length > 0 && !name.EndsWith(extension))
                name += extension;

            if (!options["replace"] && !skip_replace_check)
            {
                string title = item["title"];
                int i = 1;

                while (File.Exists(options["uploadDir"] + name))
                {
                    item["title"] = title + " (" + i + ")";
                    conf[0] = type == "auto" || type == "name" || name.IndexOf("{random}") > -1 ? type : type + " (" + i + ")";
                    name = generateFileName(conf, item, true);
                    i++;
                }
            }

            return FileUploader.FilterFilename(name);
        }

        private dynamic readListInput(string inputName = null)
        {
            if (inputName == null)
                inputName = options["listInput"] is string ? this.options["listInput"] : "fileuploader-list-" + field["name"];

            var input = Request.Form[inputName];

            if (!String.IsNullOrEmpty(input))
            {
                try
                {
                    var list = new Dictionary<string, dynamic>()
                    {
                        { "list", new List<string>() },
                        { "values", JsonConvert.DeserializeObject<List<Dictionary<string, dynamic>>>(input) }
                    };

                    foreach (Dictionary<string, dynamic> value in list["values"])
                    {
                        list["list"].Add(value["file"]);
                    }

                    return list;
                }
                catch (Exception)
                {
                    return null;
                }
            }

            return null;
        }

        private string codeToMessage(string code, dynamic item = null)
        {
            string message;

            switch (code)
            {
                case "maxRequestLength":
                    message = "The uploaded file exceeds the upload_max_filesize directive in web.config";
                    break;
                case "accepted_file_types":
                    message = "File type is not allowed for " + item["old_name"];
                    break;
                case "file_uploads":
                    message = "File uploading option in disabled in php.ini";
                    break;
                case "max_file_size":
                    message = item["old_name"] + " is too large";
                    break;
                case "max_files_size":
                    message = "Files are too big";
                    break;
                case "max_number_of_files":
                    message = "Maximum number of files is exceeded";
                    break;
                case "required_and_no_file":
                    message = "No file was choosed. Please select one";
                    break;
                case "invalid_folder_path":
                    message = "Upload folder doesn't exist or is not writable";
                    break;
                default:
                    message = "Unknown upload error";
                    break;
            }

            return message;
        }

        public static string FullDirectory(string dir)
        {
            if (dir[0] == '~' && dir[1] == '/')
                dir = HttpContext.Current.Server.MapPath(dir);

            return dir;
        }

        private string formatSize(float bytes)
        {
            if (bytes >= 1073741824)
                return (bytes / 1073741824).ToString("0.00") + " GB";
            else if (bytes >= 1048576)
                return (bytes / 1048576).ToString("0.00") + " MB";
            else if (bytes > 0)
                return (bytes / 1024).ToString("0.00") + " KB";
            else
                return "0 bytes";
        }

        private string random_string(int length)
        {
            var chars = "_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
            var stringChars = new char[length];

            for (int i = 0; i < stringChars.Length; i++)
            {
                stringChars[i] = chars[random.Next(chars.Length)];
            }

            return new String(stringChars);
        }

        public static bool Resize(string filename, dynamic maxWidth = null, dynamic maxHeight = null, dynamic destination = null, dynamic crop = null, dynamic quality = null, dynamic rotation = null)
        {
            if (!File.Exists(filename) || FileUploader.Mime_Content_Type(filename).IndexOf("image/") == -1)
                return false;

            Image image = Image.FromFile(filename);
            destination = destination ?? filename;
            int exif = Array.IndexOf(image.PropertyIdList, 274) > -1 ? image.GetPropertyItem(274).Value[0] : 1;
            decimal imageRatio = (decimal)image.Width / image.Height;

            bool hasRotation = (rotation != null && rotation != 0) || exif != 1;
            bool hasCrop = crop != null && (crop is bool ? crop == true : true);
            bool hasResizing = maxWidth != null || maxHeight != null;

            if (!hasRotation && !hasCrop && !hasResizing && filename == destination)
            {
                image.Dispose();
                return true;
            }

            if (hasRotation)
            {
                rotation = (int)rotation;

                if (exif != 1)
                {
                    switch (exif)
                    {
                        case 2:
                            image.RotateFlip(RotateFlipType.RotateNoneFlipX);
                            break;
                        case 3:
                            image.RotateFlip(RotateFlipType.Rotate180FlipNone);
                            break;
                        case 4:
                            image.RotateFlip(RotateFlipType.Rotate180FlipX);
                            break;
                        case 5:
                            image.RotateFlip(RotateFlipType.Rotate90FlipX);
                            break;
                        case 6:
                            image.RotateFlip(RotateFlipType.Rotate90FlipNone);
                            break;
                        case 7:
                            image.RotateFlip(RotateFlipType.Rotate270FlipX);
                            break;
                        case 8:
                            image.RotateFlip(RotateFlipType.Rotate270FlipNone);
                            break;
                    }

                    image.RemovePropertyItem(274);
                }

                switch (rotation)
                {
                    case 90:
                        image.RotateFlip(RotateFlipType.Rotate90FlipNone);
                        break;
                    case 180:
                        image.RotateFlip(RotateFlipType.Rotate180FlipNone);
                        break;
                    case 270:
                        image.RotateFlip(RotateFlipType.Rotate270FlipNone);
                        break;
                }
            }

            var prop = new Dictionary<string, decimal>()
            {
                { "left", 0 },
                { "top", 0 },
                { "width", image.Width },
                { "height", image.Height }
            };
            if (!(crop is bool) && crop != null)
            {
                if (crop.ContainsKey("left"))
                    prop["left"] = Math.Round((decimal)crop["left"]);
                if (crop.ContainsKey("top"))
                    prop["top"] = Math.Round((decimal)crop["top"]);
                if (crop.ContainsKey("width"))
                    prop["width"] = Math.Round((decimal)crop["width"]);
                if (crop.ContainsKey("height"))
                    prop["height"] = Math.Round((decimal)crop["height"]);
                prop["hasData"] = 1; 
            }

            decimal width = maxWidth ?? prop["width"];
            decimal height = maxHeight ?? prop["height"];
            decimal ratio = (decimal)width / height;

            if (crop is bool && crop == true)
            {
                if (maxWidth == null || maxHeight == null)
                {
                    if (imageRatio >= ratio)
                    {
                        prop["newWidth"] = prop["width"] / (prop["height"] / height);
                        prop["newHeight"] = height;
                    }
                    else
                    {
                        prop["newHeight"] = prop["height"] / (prop["width"] / width);
                        prop["newWidth"] = width;
                    }
                } else
                {
                    prop["newWidth"] = width;
                    prop["newHeight"] = height;
                }

                prop["left"] = (prop["width"] - prop["newWidth"]) / 2;
                prop["top"] = (prop["height"] - prop["newHeight"]) / 2;

                if (prop["width"] < prop["newWidth"] || prop["height"] < prop["newHeight"])
                {
                    prop["left"] = prop["width"] < prop["newWidth"] ? prop["newWidth"] / 2 - prop["width"] / 2 : 0;
                    prop["top"] = prop["height"] < prop["newHeight"] ? prop["newHeight"] / 2 - prop["height"] / 2 : 0;
                    prop["newWidth"] = prop["width"];
                    prop["newHeight"] = prop["height"];
                }

                width = prop["newWidth"];
                height = prop["newHeight"];
            }
            else if (prop["width"] < width && prop["height"] < height)
            {
                width = prop["width"];
                height = prop["height"];
            }
            else
            {
                decimal newRatio = prop["width"] / prop["height"];

                if (ratio > newRatio)
                    width = Math.Round(height * newRatio);
                else
                    height = Math.Round(width / newRatio);
            }

            int left = (int)prop["left"];
            int top = (int)prop["top"];

            if (prop.ContainsKey("newWidth"))
            {
                var rect = new Rectangle(left, top, (int)width, (int)height);
                var cr = new Bitmap((int)width, (int)height);

                using (Graphics g = Graphics.FromImage(cr))
                {
                    g.DrawImage(image, new Rectangle(0, 0, cr.Width, cr.Height), rect, GraphicsUnit.Pixel);
                }

                image.Dispose();
                image = cr;
            }

            if (prop.ContainsKey("hasData"))
            {
                var rect = new Rectangle(left, top, (int)prop["width"], (int)prop["height"]);
                var cr = new Bitmap((int)prop["width"], (int)prop["height"]);

                using (Graphics g = Graphics.FromImage(cr))
                {
                    g.DrawImage(image, new Rectangle(0, 0, cr.Width, cr.Height), rect, GraphicsUnit.Pixel);
                }

                image.Dispose();
                image = cr;
            }

            var destImage = new Bitmap((int)width, (int)height);
            using (var graphics = Graphics.FromImage(destImage))
            {
                graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
                graphics.SmoothingMode = SmoothingMode.HighQuality;
                graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;
                graphics.CompositingQuality = CompositingQuality.HighQuality;

                graphics.DrawImage(image, 0, 0, destImage.Width, destImage.Height);
            }

            var extension = Path.GetExtension(destination).Replace(".", string.Empty).ToLower();
            ImageCodecInfo format;
            var encoder = System.Drawing.Imaging.Encoder.Quality;
            EncoderParameters encoderParameters = new EncoderParameters(1);
            quality = quality ?? 100;

            switch (extension)
            {
                case "jpg":
                case "jpeg":
                    format = FileUploader.GetEncoder(ImageFormat.Jpeg);
                    break;
                case "png":
                    format = FileUploader.GetEncoder(ImageFormat.Png);
                    break;
                case "gif":
                    format = FileUploader.GetEncoder(ImageFormat.Gif);
                    break;
                default:
                    format = FileUploader.GetEncoder(ImageFormat.Jpeg);
                    break;
            }

            EncoderParameter encoderParameter = new EncoderParameter(encoder, (Int64)quality);
            encoderParameters.Param[0] = encoderParameter;

            image.Dispose();
            destImage.Save(destination, format, encoderParameters);

            destImage.Dispose();

            return true;
        }

        private static ImageCodecInfo GetEncoder(ImageFormat format)
        {
            ImageCodecInfo[] codecs = ImageCodecInfo.GetImageDecoders();
            foreach (ImageCodecInfo codec in codecs)
            {
                if (codec.FormatID == format.Guid)
                    return codec;
            }

            return null;
        }

        public static string FilterFilename(string filename)
        {
            char delimiter = '_';
            char[] invalid = { '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '<', '>', ':', '"', '/', '\\', '|', '?', '*' };

            for (int i = 0; i < invalid.Length; i++)
            {
                filename = filename.Replace(invalid[i], delimiter);
            }

            filename = Regex.Replace(filename, @"(" + delimiter + "){2,}", "$1");

            return filename;
        }

        public static void Clean_Chunked_Files(string dir, int time = 3600000)
        {
            dir = FileUploader.FullDirectory(dir);

            foreach (dynamic file in Directory.GetFiles(dir))
            {
                if (Path.GetFileName(file).IndexOf(".unconfirmed_") == 0 && File.GetCreationTime(file) < DateTime.Now.AddMilliseconds(time * -1))
                    File.Delete(file);
            }
        }

        public static string Mime_Content_Type(string filename)
        {
            string extension = Path.GetExtension(filename).Replace(".", string.Empty).ToLower();
            Dictionary<string, string> mime_types = new Dictionary<string, string>()
            {
                { "txt", "text/plain" },
                { "htm", "text/html" },
                { "html", "text/html" },
                { "php", "text/html" },
                { "css", "text/css" },
                { "js", "application/javascript" },
                { "json", "application/json" },
                { "xml", "application/xml" },
                { "swf", "application/x-shockwave-flash" },
                { "flv", "video/x-flv" },

                // images
                { "png", "image/png" },
                { "jpe", "image/jpeg" },
                { "jpeg", "image/jpeg" },
                { "jpg", "image/jpeg" },
                { "gif", "image/gif" },
                { "bmp", "image/bmp" },
                { "ico", "image/vnd.microsoft.icon" },
                { "tiff", "image/tiff" },
                { "tif", "image/tiff" },
                { "svg", "image/svg+xml" },
                { "svgz", "image/svg+xml" },

                // archives
                { "zip", "application/zip" },
                { "rar", "application/x-rar-compressed" },
                { "exe", "application/x-msdownload" },
                { "msi", "application/x-msdownload" },
                { "cab", "application/vnd.ms-cab-compressed" },

                // audio/video
                { "mp3", "audio/mpeg" },
                { "mp4", "video/mp4" },
                { "webM", "video/webm" },
                { "qt", "video/quicktime" },
                { "mov", "video/quicktime" },

                // adobe
                { "pdf", "application/pdf" },
                { "psd", "image/vnd.adobe.photoshop" },
                { "ai", "application/postscript" },
                { "eps", "application/postscript" },
                { "ps", "application/postscript" },

                // ms office
                { "doc", "application/msword" },
                { "rtf", "application/rtf" },
                { "xls", "application/vnd.ms-excel" },
                { "ppt", "application/vnd.ms-powerpoint" },

                // open office
                { "odt", "application/vnd.oasis.opendocument.text" },
                { "ods", "application/vnd.oasis.opendocument.spreadsheet" },
            };

            if (mime_types.ContainsKey(extension))
                return mime_types[extension];

            return "application/octet-stream";
        }
    }
}