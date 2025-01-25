using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using iText.Kernel.Pdf;
using iText.Kernel.Pdf.Canvas.Parser;
using iText.Kernel.Pdf.Canvas.Parser.Listener;
using System.IO;
using System;
using System.Collections.Generic;
using System.Linq;

namespace MindMapPdf.Controllers
{
    public class HomeController : Controller
    {
        private static string _pdfText = string.Empty;

        [HttpGet]
        public IActionResult Upload()
        {
            return View();
        }

        [HttpPost]
        public IActionResult Upload(IFormFile pdfFile)
        {
            if (pdfFile == null || pdfFile.Length == 0)
            {
                TempData["Error"] = "Please select a valid PDF file.";
                return RedirectToAction("Upload");
            }

            var extension = Path.GetExtension(pdfFile.FileName).ToLower();
            if (extension != ".pdf")
            {
                TempData["Error"] = "Only PDF files are allowed.";
                return RedirectToAction("Upload");
            }

            try
            {
                _pdfText = ExtractTextFromPdf(pdfFile);
                TempData["Success"] = "PDF uploaded and text extracted successfully!";
                return RedirectToAction("Viewer");
            }
            catch (Exception ex)
            {
                Console.WriteLine("Error processing PDF: " + ex.Message);
                TempData["Error"] = "An error occurred while processing the PDF.";
                return RedirectToAction("Upload");
            }
        }

        [HttpGet]
        public IActionResult Viewer()
        {
            ViewBag.PdfText = _pdfText;
            return View();
        }

        private string ExtractTextFromPdf(IFormFile pdfFile)
        {
            using var ms = new MemoryStream();
            pdfFile.CopyTo(ms);
            ms.Position = 0;

            using var pdfReader = new PdfReader(ms);
            using var pdfDoc = new PdfDocument(pdfReader);
            int numberOfPages = pdfDoc.GetNumberOfPages();

            var text = string.Empty;
            for (int i = 1; i <= numberOfPages; i++)
            {
                var page = pdfDoc.GetPage(i);
                var strategy = new SimpleTextExtractionStrategy();
                var currentPageText = PdfTextExtractor.GetTextFromPage(page, strategy);
                text += currentPageText + "\r\n";
            }

            return text;
        }
    }
}
