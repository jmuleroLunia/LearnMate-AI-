import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubjectExamsComponent } from './subject-exams.component';

describe('SubjectExamsComponent', () => {
  let component: SubjectExamsComponent;
  let fixture: ComponentFixture<SubjectExamsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SubjectExamsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SubjectExamsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
