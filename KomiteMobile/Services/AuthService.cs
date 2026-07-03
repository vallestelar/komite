using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using KomiteMobile.Core;
using KomiteMobile.Models;

namespace KomiteMobile.Services;

public sealed class AuthService : IAuthService
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);
    private readonly HttpClient _httpClient;

    public AuthService()
    {
        _httpClient = new HttpClient
        {
            BaseAddress = ApiConfiguration.BaseUri,
            Timeout = TimeSpan.FromSeconds(20),
        };
    }

    public async Task<TokenResponse> LoginAsync(
        string email,
        string password,
        CancellationToken cancellationToken = default)
    {
        var payload = new LoginRequest
        {
            Email = email.Trim(),
            Password = password,
        };

        using var response = await _httpClient.PostAsJsonAsync(
            "/api/v1/auth/login",
            payload,
            JsonOptions,
            cancellationToken);

        if (response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
        {
            throw new InvalidOperationException("Correo o contrasena incorrectos.");
        }

        response.EnsureSuccessStatusCode();

        var tokenResponse = await response.Content.ReadFromJsonAsync<TokenResponse>(
            JsonOptions,
            cancellationToken);

        return tokenResponse ?? throw new InvalidOperationException("La API no entrego una sesion valida.");
    }

    public async Task<TokenResponse> RefreshAsync(
        string refreshToken,
        CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.PostAsJsonAsync(
            "/api/v1/auth/refresh",
            new RefreshTokenRequest { RefreshToken = refreshToken },
            JsonOptions,
            cancellationToken);

        if (response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
        {
            throw new InvalidOperationException("La sesion expiro. Inicia sesion nuevamente.");
        }

        response.EnsureSuccessStatusCode();

        var tokenResponse = await response.Content.ReadFromJsonAsync<TokenResponse>(
            JsonOptions,
            cancellationToken);

        return tokenResponse ?? throw new InvalidOperationException("La API no entrego una sesion valida.");
    }

    public async Task LogoutAsync(
        string refreshToken,
        CancellationToken cancellationToken = default)
    {
        using var response = await _httpClient.PostAsJsonAsync(
            "/api/v1/auth/logout",
            new RefreshTokenRequest { RefreshToken = refreshToken },
            JsonOptions,
            cancellationToken);

        response.EnsureSuccessStatusCode();
    }
}
