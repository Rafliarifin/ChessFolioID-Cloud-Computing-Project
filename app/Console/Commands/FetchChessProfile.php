<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Http;

class FetchChessProfile extends Command
{
    // Nama command yang akan diketik di terminal
    protected $signature = 'chess:profile {username}';
    
    // Deskripsi command
    protected $description = 'Menarik data profil pemain dari Chess.com API';

    public function handle()
    {
        $username = $this->argument('username');
        $this->info("Mengambil data untuk username: {$username}...");

        // Memanggil public API gratis dari Chess.com
        $response = Http::get("https://api.chess.com/pub/player/{$username}");

        if ($response->successful()) {
            $data = $response->json();
            $this->info("Data berhasil ditemukan!");
            $this->line("--------------------------------");
            $this->line("Username : " . ($data['username'] ?? '-'));
            $this->line("Nama Asli: " . ($data['name'] ?? 'Tidak disetting'));
            $this->line("Followers: " . ($data['followers'] ?? 0));
            $this->line("Status   : " . ($data['status'] ?? '-'));
            $this->line("Link     : " . ($data['url'] ?? '-'));
            $this->line("--------------------------------");
        } else {
            $this->error("Gagal. Pemain tidak ditemukan atau terjadi kesalahan API.");
        }
    }
}