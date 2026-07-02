using KomiteMobile.Services;
using Microsoft.Maui.Controls.Shapes;

namespace KomiteMobile.Views;

public abstract class MenuListPage : ContentPage
{
    protected MenuListPage(string title, string mode, IReadOnlyList<MenuItemDefinition> items)
    {
        var sessionService = IPlatformApplication.Current?.Services.GetService<ISessionService>();
        var tenantName = sessionService?.CurrentSession?.Company?.Name ?? "Komite";
        var contextName = sessionService?.CurrentWorkspace?.DisplayName ?? "Sin condominio seleccionado";

        Title = title;
        BackgroundColor = Color.FromArgb("#F6F7F9");

        var stack = new VerticalStackLayout
        {
            Spacing = 12,
        };

        stack.Children.Add(new Label
        {
            Text = mode,
            FontSize = 13,
            TextColor = Color.FromArgb("#F79009"),
            FontAttributes = FontAttributes.Bold,
        });

        stack.Children.Add(new Label
        {
            Text = $"{tenantName} / {contextName}",
            FontSize = 13,
            TextColor = Color.FromArgb("#667085"),
        });

        stack.Children.Add(new Label
        {
            Text = title,
            FontSize = 26,
            TextColor = Color.FromArgb("#111827"),
            FontAttributes = FontAttributes.Bold,
        });

        foreach (var item in items)
        {
            stack.Children.Add(BuildMenuButton(item));
        }

        Content = new ScrollView
        {
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
                        Content = stack,
                    },
                },
            },
        };
    }

    private static Button BuildMenuButton(MenuItemDefinition item)
    {
        var button = new Button
        {
            Text = item.Title,
            HorizontalOptions = LayoutOptions.Fill,
            BackgroundColor = Color.FromArgb("#F2F4F7"),
            TextColor = Color.FromArgb("#344054"),
            CornerRadius = 8,
            Padding = new Thickness(14, 12),
        };

        button.Clicked += async (_, _) =>
        {
            if (item.Route == "logout")
            {
                var sessionService = IPlatformApplication.Current?.Services.GetService<ISessionService>();
                if (sessionService is not null)
                {
                    await sessionService.ClearAsync();
                }

                await Shell.Current.GoToAsync("//login");
                return;
            }

            await Shell.Current.GoToAsync(item.Route);
        };

        return button;
    }
}

public sealed record MenuItemDefinition(string Title, string Route);
