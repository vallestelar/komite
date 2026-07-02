using KomiteMobile.ViewModels;

namespace KomiteMobile.Views;

public partial class LoginPage : ContentPage
{
    public LoginPage()
    {
        InitializeComponent();
        BindingContext = IPlatformApplication.Current?.Services.GetService<LoginViewModel>();
    }
}
