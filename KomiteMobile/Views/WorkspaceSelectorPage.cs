using KomiteMobile.Models;
using KomiteMobile.Services;
using Microsoft.Maui.Controls.Shapes;

namespace KomiteMobile.Views;

public abstract class WorkspaceSelectorPage : ContentPage
{
    private readonly AppMode _mode;
    private readonly ISessionService? _sessionService;

    protected WorkspaceSelectorPage(AppMode mode, string title, string subtitle)
    {
        _mode = mode;
        _sessionService = IPlatformApplication.Current?.Services.GetService<ISessionService>();

        Title = title;
        Shell.SetNavBarIsVisible(this, false);
        BackgroundColor = Color.FromArgb("#F6F7F9");

        var contexts = mode == AppMode.Community
            ? _sessionService?.CommunityContexts ?? []
            : _sessionService?.OperationsContexts ?? [];

        var tenantName = _sessionService?.CurrentSession?.Company?.Name ?? "Komite";
        var stack = new VerticalStackLayout
        {
            Spacing = 14,
        };

        stack.Children.Add(BuildBackButton());

        stack.Children.Add(new Label
        {
            Text = $"Empresa: {tenantName}",
            FontSize = 14,
            TextColor = Color.FromArgb("#667085"),
            FontAttributes = FontAttributes.Bold,
        });

        stack.Children.Add(new Label
        {
            Text = title,
            FontSize = 26,
            FontAttributes = FontAttributes.Bold,
            TextColor = Color.FromArgb("#111827"),
        });

        stack.Children.Add(new Label
        {
            Text = subtitle,
            FontSize = 15,
            TextColor = Color.FromArgb("#667085"),
        });

        foreach (var context in contexts)
        {
            stack.Children.Add(BuildContextButton(context));
        }

        if (contexts.Count == 0)
        {
            stack.Children.Add(new Label
            {
                Text = "No hay condominios disponibles para este modo.",
                FontSize = 15,
                TextColor = Color.FromArgb("#B42318"),
            });
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

    private Button BuildContextButton(AppWorkspaceContext context)
    {
        var roleText = string.IsNullOrWhiteSpace(context.Condominium.RoleName)
            ? context.Condominium.Role
            : context.Condominium.RoleName;

        var button = new Button
        {
            Text = $"{context.DisplayName}\n{roleText}",
            BackgroundColor = _mode == AppMode.Community
                ? Color.FromArgb("#0B3558")
                : Color.FromArgb("#F79009"),
            TextColor = Colors.White,
            CornerRadius = 8,
            Padding = new Thickness(14, 12),
            MinimumHeightRequest = 68,
        };

        button.Clicked += async (_, _) =>
        {
            _sessionService?.SelectWorkspace(context);
            await Shell.Current.GoToAsync(_mode == AppMode.Community ? "//community" : "//operations");
        };

        return button;
    }

    private Button BuildBackButton()
    {
        var button = new Button
        {
            Text = "< Volver",
            BackgroundColor = Colors.Transparent,
            TextColor = Color.FromArgb("#0B3558"),
            FontAttributes = FontAttributes.Bold,
            Padding = new Thickness(0, 4),
            HorizontalOptions = LayoutOptions.Start,
        };

        button.Clicked += async (_, _) =>
        {
            if (_sessionService is null)
            {
                await Shell.Current.GoToAsync("//login");
                return;
            }

            var hasCommunity = _sessionService.CommunityContexts.Count > 0;
            var hasOperations = _sessionService.OperationsContexts.Count > 0;
            var backRoute = hasCommunity && hasOperations ? "//mode-selector" : "//login";
            await Shell.Current.GoToAsync(backRoute);
        };

        return button;
    }
}
