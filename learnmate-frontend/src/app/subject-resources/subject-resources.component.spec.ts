import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubjectResourcesComponent } from './subject-resources.component';

describe('SubjectResourcesComponent', () => {
  let component: SubjectResourcesComponent;
  let fixture: ComponentFixture<SubjectResourcesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SubjectResourcesComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SubjectResourcesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
