using KomiteMobile.ViewModels;
using KomiteMobile.Services;
using Microsoft.Maui.Controls.Shapes;

namespace KomiteMobile.Views;

public abstract class MenuPlaceholderPage : ContentPage
{
    protected MenuPlaceholderPage(string title, string subtitle, string mode)
    {
        var sessionService = IPlatformApplication.Current?.Services.GetService<ISessionService>();
        var tenantName = sessionService?.CurrentSession?.Company?.Name ?? "Komite";
        var contextName = sessionService?.CurrentWorkspace?.DisplayName ?? "Sin condominio seleccionado";

        Title = title;
        BindingContext = new MenuPlaceholderViewModel(title, subtitle, mode);
        BackgroundColor = Color.FromArgb("#F6F7F9");

        Content = new Grid
        {
            Padding = new Thickness(24),
            Children =
            {
                new Border
                {
                    BackgroundColor = Colors.White,
                    Stroke = Color.FromArgb("#E5E7EB"),
                    StrokeThickness = 1,
                    StrokeShape = new RoundRectangle { CornerRadius = 8 },
                    Padding = new Thickness(18),
                    VerticalOptions = LayoutOptions.Start,
                    Content = new VerticalStackLayout
                    {
                        Spacing = 10,
                        Children =
                        {
                            new Label
                            {
                                Text = mode,
                                FontSize = 13,
                                TextColor = Color.FromArgb("#F79009"),
                                FontAttributes = FontAttributes.Bold,
                            },
                            new Label
                            {
                                Text = $"{tenantName} / {contextName}",
                                FontSize = 13,
                                TextColor = Color.FromArgb("#667085"),
                            },
                            new Label
                            {
                                Text = title,
                                FontSize = 26,
                                TextColor = Color.FromArgb("#111827"),
                                FontAttributes = FontAttributes.Bold,
                            },
                            new Label
                            {
                                Text = subtitle,
                                FontSize = 15,
                                TextColor = Color.FromArgb("#667085"),
                            },
                            new Label
                            {
                                Text = "Pantalla base creada. Aqui iremos conectando la informacion real de la API.",
                                FontSize = 14,
                                TextColor = Color.FromArgb("#98A2B3"),
                                Margin = new Thickness(0, 12, 0, 0),
                            },
                        },
                    },
                },
            },
        };
    }
}
