namespace KomiteMobile.ViewModels;

public sealed class MenuPlaceholderViewModel : ViewModelBase
{
    public MenuPlaceholderViewModel(string title, string subtitle, string mode)
    {
        Title = title;
        Subtitle = subtitle;
        Mode = mode;
    }

    public string Title { get; }

    public string Subtitle { get; }

    public string Mode { get; }
}
