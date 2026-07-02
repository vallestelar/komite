using KomiteMobile.Services;

namespace KomiteMobile.Views;

public sealed class ModeSelectorPage : ContentPage
{
    private readonly ISessionService? _sessionService;

    public ModeSelectorPage()
    {
        _sessionService = IPlatformApplication.Current?.Services.GetService<ISessionService>();

        Title = "Modo";
        Shell.SetNavBarIsVisible(this, false);
        BackgroundColor = Color.FromArgb("#F6F7F9");

        var tenantName = _sessionService?.CurrentSession?.Company?.Name ?? "Komite";
        var communityButton = BuildButton("Comunidad", "Vecinos y comite", "#0B3558");
        communityButton.IsEnabled = (_sessionService?.CommunityContexts.Count ?? 0) > 0;
        communityButton.Clicked += async (_, _) => await GoToCommunityAsync();

        var operationsButton = BuildButton("Operacion", "Empresa y terreno", "#F79009");
        operationsButton.IsEnabled = (_sessionService?.OperationsContexts.Count ?? 0) > 0;
        operationsButton.Clicked += async (_, _) => await Shell.Current.GoToAsync("//operations-context-selector");

        var content = new VerticalStackLayout
        {
            Spacing = 18,
            MaximumWidthRequest = 420,
            HorizontalOptions = LayoutOptions.Fill,
            Children =
            {
                new Image
                {
                    Source = "komite_logo.png",
                    HeightRequest = 160,
                    WidthRequest = 240,
                    Aspect = Aspect.AspectFit,
                    HorizontalOptions = LayoutOptions.Center,
                },
                new Label
                {
                    Text = $"Empresa: {tenantName}",
                    FontSize = 14,
                    FontAttributes = FontAttributes.Bold,
                    TextColor = Color.FromArgb("#667085"),
                    HorizontalTextAlignment = TextAlignment.Center,
                },
                new Label
                {
                    Text = "Selecciona como quieres entrar",
                    FontSize = 24,
                    FontAttributes = FontAttributes.Bold,
                    TextColor = Color.FromArgb("#111827"),
                    HorizontalTextAlignment = TextAlignment.Center,
                },
                communityButton,
                operationsButton,
            },
        };

        Grid.SetRow(content, 1);

        Content = new Grid
        {
            Padding = new Thickness(24),
            RowDefinitions =
            {
                new RowDefinition(GridLength.Star),
                new RowDefinition(GridLength.Auto),
                new RowDefinition(GridLength.Star),
            },
            Children = { content },
        };
    }

    private async Task GoToCommunityAsync()
    {
        if (_sessionService is null)
        {
            return;
        }

        if (_sessionService.CommunityContexts.Count == 1)
        {
            _sessionService.SelectWorkspace(_sessionService.CommunityContexts[0]);
            await Shell.Current.GoToAsync("//community");
            return;
        }

        await Shell.Current.GoToAsync("//community-context-selector");
    }

    private static Button BuildButton(string title, string subtitle, string color)
    {
        return new Button
        {
            Text = $"{title}\n{subtitle}",
            BackgroundColor = Color.FromArgb(color),
            TextColor = Colors.White,
            CornerRadius = 8,
            FontSize = 16,
            Padding = new Thickness(16, 14),
            MinimumHeightRequest = 68,
        };
    }
}
