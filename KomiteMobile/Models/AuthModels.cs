using System.Text.Json.Serialization;

namespace KomiteMobile.Models;

public sealed class LoginRequest
{
    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;

    [JsonPropertyName("password")]
    public string Password { get; set; } = string.Empty;
}

public sealed class TokenResponse
{
    [JsonPropertyName("access_token")]
    public string AccessToken { get; set; } = string.Empty;

    [JsonPropertyName("token_type")]
    public string TokenType { get; set; } = "bearer";

    [JsonPropertyName("user")]
    public UserLoginResponse User { get; set; } = new();

    [JsonPropertyName("company")]
    public CompanyLoginResponse? Company { get; set; }

    [JsonPropertyName("condominiums")]
    public List<CondominiumLoginResponse> Condominiums { get; set; } = [];
}

public sealed class UserLoginResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;

    [JsonPropertyName("full_name")]
    public string FullName { get; set; } = string.Empty;

    [JsonPropertyName("global_role")]
    public string? GlobalRole { get; set; }
}

public sealed class CompanyLoginResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;
}

public sealed class CondominiumLoginResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("role_name")]
    public string RoleName { get; set; } = string.Empty;

    [JsonPropertyName("unit_id")]
    public string? UnitId { get; set; }

    [JsonPropertyName("unit_identifier")]
    public string? UnitIdentifier { get; set; }
}
