namespace MindMapPdf.Models
{
    /// <summary>
    /// Represents a user explanation tied to a specific phrase in the PDF text.
    /// </summary>
    public class Explanation
    {
        public int Id { get; set; }
        public string Phrase { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
    }
}
