using KomiteMobile.Models;

namespace KomiteMobile.Services;

public interface IAuthService
{
    Task<TokenResponse> LoginAsync(string email, string password, CancellationToken cancellationToken = default);

    Task<TokenResponse> RefreshAsync(string refreshToken, CancellationToken cancellationToken = default);

    Task LogoutAsync(string refreshToken, CancellationToken cancellationToken = default);
}
