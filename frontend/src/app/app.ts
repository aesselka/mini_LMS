import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Header } from './components/header/header';
import { CapybaraPet } from './components/capybara-pet/capybara-pet';
import { PreferencesService } from './services/preferences.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, CapybaraPet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected prefs = inject(PreferencesService);
}
