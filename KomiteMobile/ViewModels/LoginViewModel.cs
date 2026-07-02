using System.Windows.Input;
using KomiteMobile.Services;

namespace KomiteMobile.ViewModels;

public sealed class LoginViewModel : ViewModelBase
{
    private readonly IAuthService _authService;
    private readonly ISessionService _sessionService;
    private string _email = string.Empty;
    private string _password = string.Empty;
    private string _errorMessage = string.Empty;
    private bool _isBusy;

    public LoginViewModel(IAuthService authService, ISessionService sessionService)
    {
        _authService = authService;
        _sessionService = sessionService;
        LoginCommand = new AsyncCommand(LoginAsync, CanLogin);
    }

    public string Email
    {
        get => _email;
        set
        {
            if (SetProperty(ref _email, value))
            {
                NotifyLoginStateChanged();
            }
        }
    }

    public string Password
    {
        get => _password;
        set
        {
            if (SetProperty(ref _password, value))
            {
                NotifyLoginStateChanged();
            }
        }
    }

    public string ErrorMessage
    {
        get => _errorMessage;
        private set
        {
            if (SetProperty(ref _errorMessage, value))
            {
                OnPropertyChanged(nameof(HasError));
            }
        }
    }

    public bool HasError => !string.IsNullOrWhiteSpace(ErrorMessage);

    public bool CanSubmit => CanLogin();

    public bool IsBusy
    {
        get => _isBusy;
        private set
        {
            if (SetProperty(ref _isBusy, value))
            {
                NotifyLoginStateChanged();
            }
        }
    }

    public ICommand LoginCommand { get; }

    private bool CanLogin()
    {
        return !IsBusy
            && !string.IsNullOrWhiteSpace(Email)
            && !string.IsNullOrWhiteSpace(Password);
    }

    private async Task LoginAsync()
    {
        ErrorMessage = string.Empty;
        IsBusy = true;

        try
        {
            var session = await _authService.LoginAsync(Email, Password);
            await _sessionService.SaveAsync(session);
            await Shell.Current.GoToAsync(_sessionService.ResolveInitialRoute());
        }
        catch (InvalidOperationException ex)
        {
            ErrorMessage = ex.Message;
        }
        catch (HttpRequestException)
        {
            ErrorMessage = "No se pudo conectar con la API.";
        }
        catch (TaskCanceledException)
        {
            ErrorMessage = "La API no respondio a tiempo.";
        }
        finally
        {
            IsBusy = false;
        }
    }

    private void NotifyLoginStateChanged()
    {
        OnPropertyChanged(nameof(CanSubmit));

        if (LoginCommand is AsyncCommand command)
        {
            command.RaiseCanExecuteChanged();
        }
    }
}
